# AI-Enhanced Real-Time Occupancy Planning System (Streamlit Prototype with Ollama)

This project is a Streamlit prototype demonstrating an AI-powered system for finding available workspaces based on natural language queries. It integrates mock data representing real-time occupancy, desk inventory, and organizational policies, **using a local Ollama instance for Natural Language Processing (NLP)**.

## Features

*   **Natural Language Query Input:** Users can enter requests in plain English (e.g., "Find me a standing desk near marketing for tomorrow afternoon").
*   **AI-Powered Parsing (Ollama):** Uses a locally running Ollama instance (e.g., with `llama3`, `mistral`, or `phi3`) to parse the natural language query into structured search criteria (desk type, location, time, etc.). Requires Ollama server to be running locally.
*   **Data Integration:** Loads mock data for:
    *   Building/Floor/Zone/Area structure (`spaces.json`)
    *   Desk inventory with features and status (`desks.json`)
    *   Simulated real-time occupancy and forecasts (`occupancy.json`)
    *   Organizational policies and rules (`policies.json`)
*   **Filtering Logic:** Filters available desks based on parsed criteria (type, floor, proximity).
*   **Availability Check:** Performs a basic availability check considering:
    *   Desk status (e.g., "maintenance").
    *   Forecasted area occupancy for future requests (e.g., "tomorrow afternoon").
    *   Simple policy checks (e.g., area capacity limits).
*   **Workspace Recommendation:** Recommends suitable desks that match the criteria and availability checks.
*   **Streamlit UI:** Provides a simple web interface for interaction.

## Prerequisites

*   Python 3.8+
*   `pip` (Python package installer)
*   **Ollama:** You need Ollama installed and running locally.
    *   Download and install from [https://ollama.com/](https://ollama.com/)
    *   Ensure the Ollama server is running (usually starts automatically after installation, or run `ollama serve` in the terminal).
*   **Ollama Model:** You need a suitable model pulled for Ollama that supports JSON output. `llama3` is recommended. Pull it using:
    ```bash
    ollama pull llama3
    ```
    *(Other models like `mistral` or `phi3` might also work if they support the JSON format flag).*

## Setup Instructions

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd occupancy-planner-streamlit
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Verify Ollama Setup:**
    *   Make sure the Ollama application is running.
    *   Confirm you have pulled the required model (e.g., `ollama list` should show `llama3`).
    *   The application defaults to connecting to `http://localhost:11434`. If your Ollama runs on a different port/address, set the `OLLAMA_API_URL` environment variable. You can also set `OLLAMA_MODEL` if you want to use a different model than `llama3`.

5.  **Verify Mock Data:**
    Ensure the `data/` directory exists and contains the required JSON files: `spaces.json`, `occupancy.json`, `desks.json`, `employee_preferences.json`, and `policies.json`.

## Running the Application

1.  **Ensure Ollama is running** with the necessary model available.
2.  **Activate your virtual environment** (if you created one).
3.  **(Optional) Set Environment Variables:** If your Ollama setup differs from the default:
    ```bash
    # Example: Using a different model
    export OLLAMA_MODEL=mistral
    # Example: Ollama running on a different port
    export OLLAMA_API_URL=http://localhost:11435/api/generate
    ```
4.  **Run the Streamlit app:**
    ```bash
    streamlit run app.py
    ```
5.  Open your web browser and navigate to the local URL provided by Streamlit (usually `http://localhost:8501`). The app will check the connection to Ollama on startup.

## How to Use

1.  Enter your workspace request in the text box. The default query is provided as an example.
2.  Click the "Find Workspace" button.
3.  The application will:
    *   Attempt to parse your query using your local Ollama instance. The extracted criteria will be shown.
    *   Filter the available desks based on the criteria. A log of filtering steps can be expanded.
    *   Check the availability of the filtered desks based on their status and relevant forecasts/policies. An availability log can be expanded.
    *   Display recommended desks or a message if no suitable desks are found.

## Mock Data Explanation

*   **`spaces.json`**: Defines the physical hierarchy (building, floors, zones, areas) with names and capacities.
*   **`occupancy.json`**: Contains mock real-time occupancy counts/percentages per area (`occupancy_data`) and forecasted occupancy percentages for the next day (`forecast`).
*   **`desks.json`**: Lists individual desks with their ID, type, location (area, floor, zone), features, current status, and last used timestamp. `vergesense_area_id` links to the occupancy data.
*   **`employee_preferences.json`**: (Not actively used in the core logic for the specific query but included for future expansion) Contains employee preferences for desk types, locations, equipment, etc.
*   **`policies.json`**: Defines organizational rules like capacity limits, sanitization requirements, and team zoning preferences.

## Limitations & Future Improvements

*   **Dependency on Local Ollama:** Requires users to install, run, and manage their own Ollama instance and models.
*   **NLP Accuracy:** The accuracy of the NLP parsing depends heavily on the chosen Ollama model and its ability to follow instructions and generate structured JSON correctly. Prompt engineering might be needed for different models.
*   **Performance:** Local model inference speed depends on the user's hardware. Requests might take longer than cloud-based APIs.
*   **Availability Simplification:** The availability check for future times ("tomorrow afternoon") is based on *area forecast* percentages, not individual desk bookings. It assumes desks *might* be free if the area isn't fully occupied according to the forecast. A real system requires integration with a booking calendar.
*   **Policy Implementation:** Only basic policy checks (capacity limits) are actively used in filtering. More complex policies (sanitization time gaps, social distancing) require more sophisticated logic and data.
*   **Proximity Logic:** Only proximity to "marketing team" (based on Marketing Zone areas) is specifically implemented. Other proximity requests (e.g., "near window") are not handled.
*   **Error Handling:** Basic error handling for Ollama connection and response parsing is included, but robustness could be improved.
*   **Employee Preferences:** Not currently factored into the recommendation ranking for this specific query.
*   **Scalability:** Data loading and filtering are done in memory. For larger datasets, databases and more optimized querying would be necessary.