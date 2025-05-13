import streamlit as st
import json
import os
import requests # Added for Ollama interaction
from pathlib import Path
import time # For simple connection check backoff

# --- Configuration ---
DATA_DIR = Path("data")
SPACES_FILE = DATA_DIR / "spaces.json"
OCCUPANCY_FILE = DATA_DIR / "occupancy.json"
DESKS_FILE = DATA_DIR / "desks.json"
EMPLOYEE_PREFS_FILE = DATA_DIR / "employee_preferences.json" # Not used in this specific query logic, but loaded for future use
POLICIES_FILE = DATA_DIR / "policies.json"

# --- Ollama Configuration ---
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate") # Default Ollama API endpoint
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:mini") # Changed from llama3 due to timeout issues - Default model - make sure you have pulled this model (ollama pull llama3)
NLP_ENABLED = False # Flag to indicate if NLP service is available

# --- Check Ollama Connection ---
@st.cache_resource(ttl=60) # Cache the check result for 60 seconds
def check_ollama_connection(url):
    """Checks if the Ollama server is reachable."""
    try:
        # Send a lightweight request, e.g., just check if the endpoint exists or get models list
        # Using a simple GET request to base URL often works for basic health check
        ping_url = url.replace("/api/generate", "") # Get base URL
        response = requests.get(ping_url, timeout=3) # Short timeout
        # A more robust check might be to list models: requests.get(url.replace("/api/generate", "/api/tags"))
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        print("Ollama connection successful.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Ollama connection failed: {e}")
        return False

# Perform the check only once per session unless cache expires
if 'ollama_checked' not in st.session_state:
     with st.spinner("Checking connection to local Ollama server..."):
        NLP_ENABLED = check_ollama_connection(OLLAMA_API_URL)
        st.session_state.ollama_checked = True
        st.session_state.nlp_enabled = NLP_ENABLED # Store in session state
else:
    NLP_ENABLED = st.session_state.nlp_enabled # Retrieve from session state

if not NLP_ENABLED:
     st.warning(f"Could not connect to Ollama server at {OLLAMA_API_URL}. "
               f"Ensure Ollama is running and the model '{OLLAMA_MODEL}' is available. "
               "NLP features will be disabled.", icon="")

# --- Helper Functions ---

@st.cache_data  # Cache the data loading
def load_json_data(file_path):
    """Loads JSON data from a file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Error: Data file not found at {file_path}")
        return None
    except json.JSONDecodeError:
        st.error(f"Error: Could not decode JSON from {file_path}")
        return None

def get_structured_query_from_nlp(natural_language_query):
    """
    Uses a local Ollama instance to parse the natural language query into a structured JSON object.
    """
    if not NLP_ENABLED:
         st.error("Ollama connection is not available. Cannot parse natural language query.")
         return None

    system_prompt = """
    You are an AI assistant helping parse user requests for finding workspaces.
    Your task is to extract key information from the user's query and return it as a JSON object.
    Focus on extracting the following fields if present:
    - desk_type: (e.g., "standing", "regular")
    - location_proximity: (e.g., "marketing team", "window", "quiet area") - specify the target of proximity.
    - floor: (e.g., "3rd", "2nd", number)
    - time_request: (e.g., "tomorrow afternoon", "now", "next Monday morning")
    - specific_features: (e.g., ["dual-monitor", "ergonomic-chair"]) - list any specific equipment mentioned.

    If a field is not mentioned, omit it from the JSON output.
    Respond ONLY with the JSON object, nothing else before or after.

    User Query: "{query}"
    JSON Output:
    """
    print(f"natural_language_query: {natural_language_query}")
    full_prompt = system_prompt.format(query=natural_language_query)

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "format": "json",  # Request JSON output directly
        "stream": False   # We want the full response at once
    }

    try:
        print(f"OLLAMA_API_URL: {OLLAMA_API_URL}")
        print(f"payload: {payload}")

        response = requests.post(OLLAMA_API_URL, json=payload, timeout=120) # Increased timeout for generation
        response.raise_for_status()  # Raise an exception for bad status codes

        response_data = response.json()
        # Ollama's response with format="json" should directly contain the JSON string in the 'response' field
        json_string = response_data.get("response")

        if not json_string:
             st.error(f"Ollama response did not contain the expected 'response' field. Full response: {response_data}")
             return None

        # Parse the JSON string returned by Ollama
        return json.loads(json_string)

    except requests.exceptions.Timeout:
         st.error(f"Request to Ollama timed out. The server might be busy or the model is taking too long.")
         return None
    except requests.exceptions.ConnectionError:
         st.error(f"Could not connect to Ollama server at {OLLAMA_API_URL}. Is it running?")
         # Optionally disable NLP for the rest of the session
         st.session_state.nlp_enabled = False
         st.rerun() # Rerun to show the warning
         return None
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred during the Ollama API call: {e}")
        # Optionally disable NLP
        st.session_state.nlp_enabled = False
        st.rerun()
        return None
    except json.JSONDecodeError as e:
        st.error(f"Ollama returned a response, but it was not valid JSON. Response text: '{json_string}'. Error: {e}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred while processing the Ollama response: {e}")
        return None


def find_marketing_zone_areas(spaces_data):
    """Finds the area IDs associated with the Marketing Zone."""
    marketing_zone_id = None
    for space in spaces_data.get("spaces", []):
        if space.get("name") == "Marketing Zone" and space.get("type") == "zone":
            marketing_zone_id = space.get("id")
            break

    if not marketing_zone_id:
        return []

    marketing_area_ids = []
    for space in spaces_data.get("spaces", []):
        if space.get("parent_id") == marketing_zone_id and space.get("type") == "area":
            marketing_area_ids.append(space.get("id"))

    return marketing_area_ids

def check_desk_availability(desk, time_request, occupancy_data, policies):
    """
    Checks if a desk is likely available based on status and forecast.
    Simplification: For "tomorrow afternoon", checks forecast. Ignores specific booking times.
    """
    # 1. Check current status - Maintenance blocks immediately
    if desk.get("status") == "maintenance":
        return False, "Desk is under maintenance."

    # 2. Check forecast for "tomorrow afternoon"
    if time_request == "tomorrow afternoon":
        area_id = desk.get("vergesense_area_id")
        forecast_data = occupancy_data.get("forecast", {}).get(area_id, {}).get("next_day", {})
        forecast = forecast_data.get("afternoon") # Directly access "afternoon"


        if forecast is None:
            # No forecast data for this area/time - conservative approach: assume unavailable
             return False, f"No 'afternoon' forecast data available for Area {area_id} tomorrow."

        # Check against capacity limits policy (e.g., POL-005 threshold)
        capacity_policy = next((p for p in policies.get("policies", []) if p.get("id") == "POL-005"), None)
        threshold = 80 # Default threshold if policy not found or doesn't specify numeric limit easily
        if capacity_policy and "80%" in capacity_policy.get("description", ""): # Simple check
             threshold = 80

        if forecast >= threshold:
             return False, f"Area {area_id} forecasted occupancy ({forecast}%) meets/exceeds threshold ({threshold}%) for tomorrow afternoon."

        # Desk Sanitization Policy (POL-002) - Simple check: Not implemented in detail for prototype
        # For "tomorrow afternoon", this is unlikely to conflict unless used very late today.

        # If forecast is below threshold, we *assume* the desk *might* be available.
        # A real system needs actual booking data.
        return True, f"Area {area_id} forecast ({forecast}%) is below threshold ({threshold}%) for tomorrow afternoon. Desk *may* be available."

    # 3. Handle other time requests (e.g., "now") - simplified: check current status
    elif time_request == "now": # Example for extendibility
        if desk.get("status") == "available":
            return True, "Desk is currently available."
        else:
            return False, f"Desk status is currently '{desk.get('status')}'."
    else:
        # Time request not handled by this prototype's logic
        return False, f"Availability check for '{time_request}' not implemented."


# --- Load Data ---
# Attempt to load data only if not already loaded and errored
if 'data_loaded' not in st.session_state:
    spaces_data = load_json_data(SPACES_FILE)
    occupancy_data = load_json_data(OCCUPANCY_FILE)
    desks_data = load_json_data(DESKS_FILE)
    employee_prefs_data = load_json_data(EMPLOYEE_PREFS_FILE) # Load if needed later
    policies_data = load_json_data(POLICIES_FILE)
    st.session_state.data_loaded = True # Mark data as loaded (or attempted)
    st.session_state.spaces_data = spaces_data
    st.session_state.occupancy_data = occupancy_data
    st.session_state.desks_data = desks_data
    st.session_state.policies_data = policies_data
    st.session_state.employee_prefs_data = employee_prefs_data
else:
    spaces_data = st.session_state.spaces_data
    occupancy_data = st.session_state.occupancy_data
    desks_data = st.session_state.desks_data
    policies_data = st.session_state.policies_data
    employee_prefs_data = st.session_state.employee_prefs_data


# --- Streamlit UI ---
#st.set_page_config(layout="wide")
st.title("AI-Enhanced Real-Time Occupancy Planning System ✨")
st.markdown("Prototype focusing on Natural Language Queries for Workspace Allocation (using local Ollama).")

# Input Query
default_query = "Find me an available standing desk near the marketing team on the 3rd floor for tomorrow afternoon."
nl_query = st.text_input("Enter your workspace request:", value=default_query)

if st.button("Find Workspace"):
    if not nl_query:
        st.warning("Please enter a query.")
    elif not all([spaces_data, occupancy_data, desks_data, policies_data]):
         st.error("Could not load all necessary data files. Please check the `data` directory and restart.")
    elif not NLP_ENABLED:
         st.error("Ollama NLP features are disabled (connection failed or not configured). Cannot process the request.")
    else:
        with st.spinner("Processing your request... (Parsing Query -> Filtering Desks -> Checking Availability)"):

            # 1. Parse Natural Language Query using AI
            st.subheader("1. Parsing Natural Language Query (via Ollama)")
            structured_query = get_structured_query_from_nlp(nl_query)

            if not structured_query:
                st.error("Failed to parse the natural language query using Ollama.")
            else:
                st.json(structured_query) # Display the JSON output from Ollama

                # Extract criteria (handle potential missing keys)
                req_desk_type = structured_query.get("desk_type")
                req_proximity = structured_query.get("location_proximity")
                req_floor_str = structured_query.get("floor")
                req_time = structured_query.get("time_request", "now") # Default to 'now' if not specified

                # Convert floor string to integer if possible
                req_floor = None
                if req_floor_str:
                    try:
                        # Extract digits from floor string (e.g., "3rd" -> 3)
                        req_floor = int(''.join(filter(str.isdigit, str(req_floor_str)))) # Ensure it's a string first
                    except ValueError:
                        st.warning(f"Could not parse floor '{req_floor_str}' as a number.")


                # 2. Filter Desks based on Structured Query
                st.subheader("2. Filtering Desks")
                 # Ensure desks_data is not None before proceeding
                if desks_data is None:
                    st.error("Desks data is not loaded. Cannot filter.")
                else:
                    candidate_desks = desks_data.get("desks", [])
                    filtered_desks = []
                    filter_log = [] # Log reasons for filtering

                    # --- Filtering Steps ---
                    initial_count = len(candidate_desks)
                    filter_log.append(f"Starting with {initial_count} total desks.")

                    # Filter by Type
                    if req_desk_type:
                        candidate_desks = [d for d in candidate_desks if d.get("type") == req_desk_type]
                        filter_log.append(f"Filtered by type '{req_desk_type}': {len(candidate_desks)} remaining.")

                    # Filter by Floor
                    if req_floor is not None:
                        candidate_desks = [d for d in candidate_desks if d.get("floor") == req_floor]
                        filter_log.append(f"Filtered by floor '{req_floor}': {len(candidate_desks)} remaining.")

                    # Filter by Proximity (Marketing Team specific implementation)
                    if req_proximity and req_proximity.lower() == "marketing team":
                        if spaces_data: # Check if spaces_data loaded correctly
                            marketing_area_ids = find_marketing_zone_areas(spaces_data)
                            if not marketing_area_ids:
                                filter_log.append("Warning: Could not find areas associated with 'Marketing Zone'. Skipping proximity filter.")
                            else:
                                candidate_desks = [d for d in candidate_desks if d.get("area_id") in marketing_area_ids]
                                filter_log.append(f"Filtered by proximity to 'Marketing Team' (Areas: {', '.join(marketing_area_ids)}): {len(candidate_desks)} remaining.")
                        else:
                             filter_log.append("Warning: Spaces data not loaded, cannot filter by proximity.")
                    elif req_proximity:
                        filter_log.append(f"Note: Proximity filter for '{req_proximity}' not specifically implemented in this prototype.")


                    # --- Log Filtering Steps ---
                    with st.expander("Filtering Log"):
                        for log_entry in filter_log:
                            st.write(log_entry)
                        st.write(f"**Candidate desks after initial filters:** {len(candidate_desks)}")
                        if candidate_desks:
                            st.dataframe(candidate_desks, use_container_width=True)


                    # 3. Check Availability & Policies for remaining candidates
                    st.subheader("3. Checking Availability & Policies")
                    available_desks = []
                    availability_log = []

                    if not candidate_desks:
                        st.info("No desks match the initial filter criteria (Type, Floor, Proximity).")
                    elif occupancy_data is None or policies_data is None:
                         st.error("Occupancy or Policies data not loaded. Cannot check availability.")
                    else:
                        for desk in candidate_desks:
                            is_available, reason = check_desk_availability(desk, req_time, occupancy_data, policies_data)
                            availability_log.append(f"Desk {desk.get('id')}: Available = {is_available}. Reason: {reason}")
                            if is_available:
                                available_desks.append(desk)

                        with st.expander("Availability Check Log"):
                            for log_entry in availability_log:
                                st.write(log_entry)

                    # 4. Return Recommendations
                    st.subheader("4. Workspace Recommendations")
                    if available_desks:
                        st.success(f"Found {len(available_desks)} potentially suitable desk(s) for '{req_time}':")

                        # Simple Recommendation: Show the first few available desks
                        st.dataframe(available_desks, use_container_width=True)

                        # Provide details of the first recommendation
                        st.markdown("---")
                        st.markdown(f"**Top Recommendation:** Desk **{available_desks[0].get('id')}**")
                        st.markdown(f"*   **Location:** {available_desks[0].get('location_description', 'N/A')}")
                        st.markdown(f"*   **Area:** {available_desks[0].get('area_id')} ({available_desks[0].get('zone')})")
                        st.markdown(f"*   **Type:** {available_desks[0].get('type')}")
                        st.markdown(f"*   **Features:** {', '.join(available_desks[0].get('features', []))}")
                        # Add the positive availability reason
                        if occupancy_data and policies_data:
                             _ , positive_reason = check_desk_availability(available_desks[0], req_time, occupancy_data, policies_data)
                             st.markdown(f"*   **Availability Note:** {positive_reason}")


                    else:
                        st.warning("Sorry, no desks matching all your criteria and availability constraints were found.")

# Optional: Display loaded data for transparency/debugging
st.sidebar.subheader("Loaded Mock Data")
if spaces_data and st.sidebar.checkbox("Show Spaces Data"):
    st.sidebar.json(spaces_data)
if occupancy_data and st.sidebar.checkbox("Show Occupancy/Forecast Data"):
    st.sidebar.json(occupancy_data)
if desks_data and st.sidebar.checkbox("Show Desks Data"):
    st.sidebar.json(desks_data)
if policies_data and st.sidebar.checkbox("Show Policies Data"):
    st.sidebar.json(policies_data)
if policies_data and st.sidebar.checkbox("Show Employee Preferences Data"):
    st.sidebar.json(employee_prefs_data)