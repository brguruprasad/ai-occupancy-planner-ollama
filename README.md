# AI-Enhanced Real-Time Occupancy Planning System (Streamlit + Ollama)

This project is a Streamlit prototype demonstrating an AI-powered system for finding available workspaces based on natural language queries. It integrates mock data representing building spaces, desk inventory, real-time occupancy, and organizational policies, using a **local Ollama instance** for Natural Language Processing (NLP).

## Features

*   **Natural Language Query Input:** Users can enter requests in plain English (e.g., "Find me a standing desk near marketing for tomorrow afternoon").
*   **AI-Powered Parsing (Ollama):** Uses a locally running Ollama instance to parse the natural language query into structured search criteria.
*   **Data Integration:** Loads mock data for spaces, desks, occupancy, and policies.
*   **Dynamic Filtering:** Filters desks based on parsed criteria (type, floor, proximity).
*   **Availability Check:** Performs basic availability checks using desk status and forecasted area occupancy.
*   **Workspace Recommendation:** Suggests suitable desks.
*   **Streamlit UI:** Provides an interactive web interface.

## Prerequisites

*   Python 3.8+
*   `pip` (Python package installer)
*   **Ollama:**
    *   Installed and running locally (Download from [https://ollama.com/](https://ollama.com/)).
    *   Ollama server must be active (usually starts automatically or run `ollama serve`).
*   **Ollama Model:** A suitable language model pulled for Ollama. Recommended lightweight options:
    *   `phi3:mini` (Fastest, good starting point)
    *   `mistral:7b` (Good balance of speed and capability)
    *   Pull a model using: `ollama pull phi3:mini` or `ollama pull mistral:7b`

## Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git
    cd YOUR_REPOSITORY_NAME
    ```
    *(Replace YOUR_USERNAME and YOUR_REPOSITORY_NAME)*

2.  **Create and Activate a Virtual Environment (Recommended):**
    ```bash
    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Verify Ollama Setup:**
    *   Ensure the Ollama application/server is running.
    *   Confirm you have pulled a model. Check with: `ollama list`. You should see the model you intend to use (e.g., `phi3:mini`).
    *   The application defaults to connecting to Ollama at `http://localhost:11434` and using the model specified in `app.py` (defaults to `phi3:mini`).

5.  **(Optional) Configure Ollama Connection:**
    If your Ollama setup differs or you want to use a different model by default without changing the code, you can set environment variables *before* running the app:
    *   `OLLAMA_API_URL`: e.g., `http://localhost:11435/api/generate` (if Ollama is on a different port)
    *   `OLLAMA_MODEL`: e.g., `mistral:7b`

## Running the Application

1.  **Ensure Ollama is running** with your chosen model loaded/available.
2.  **Activate your virtual environment** (if you created one).
3.  **(Optional) Set environment variables** as described above if needed.
4.  **Run the Streamlit app from the project's root directory:**
    ```bash
    streamlit run app.py 
    or
    python -m streamlit run app.py
    ```
5.  Open your web browser and navigate to the local URL provided by Streamlit (usually `http://localhost:8501`).
    The application will attempt to connect to Ollama on startup.

## How to Use

1.  Once the app is running, you'll see an input field: "Enter your workspace request:".
2.  Type your query in natural language (e.g., "Find me an available standing desk near the marketing team on the 3rd floor for tomorrow afternoon.").
3.  Click the "Find Workspace" button.
4.  The application will:
    *   **Parse Query:** Send your request to your local Ollama instance to extract structured criteria (shown on the UI).
    *   **Filter Desks:** Apply these criteria to the mock desk data.
    *   **Check Availability:** Evaluate if the filtered desks are likely available based on their status and forecasted occupancy.
    *   **Recommend:** Display suitable desks or a message if none are found.
5.  You can view details of the filtering and availability check process by expanding the respective sections.
6.  The sidebar allows you to inspect the raw mock data loaded by the application.

## Project Structure