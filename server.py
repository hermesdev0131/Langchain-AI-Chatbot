from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder='static')

# Langflow API Configuration
LANGFLOW_BASE_URL = "https://api.langflow.astra.datastax.com"
LANGFLOW_FLOW_ID = "9bd61166-c8f5-45a8-a3bf-9727a42673a6"
LANGFLOW_LANGFLOW_ID = "7bc06c0e-d5c5-4097-b6f7-419630908d27"
LANGFLOW_TOKEN = os.getenv("LANGFLOW_TOKEN")

# Serve the static index.html
@app.route('/', methods=['GET'])
def serve_index():
    return app.send_static_file('index.html')

# Handle POST requests from the front-end
@app.route('/', methods=['POST'])
def handle_post():
    data = request.get_json()
    user_message = data.get('userMessage', 'No message provided')

    # Langflow API endpoint
    langflow_url = f"{LANGFLOW_BASE_URL}/lf/{LANGFLOW_LANGFLOW_ID}/api/v1/run/{LANGFLOW_FLOW_ID}?stream=false"

    # Prepare request payload for Langflow
    payload = {
        "input_value": user_message,
        "input_type": "chat",
        "output_type": "chat",
        "tweaks": {
            "ChatInput-c0GWz": {},
            "ParseData-u0Fdc": {},
            "Prompt-xMFy9": {},
            "SplitText-U0vYs": {},
            "OpenAIModel-78wQr": {},
            "ChatOutput-v7nrP": {},
            "AstraDB-U4a6k": {},
            "OpenAIEmbeddings-MmZEF": {},
            "AstraDB-dNPtJ": {},
            "OpenAIEmbeddings-397sQ": {},
            "URL-MvVXJ": {}
        }
    }

    # Add authorization headers for Langflow API
    headers = {
        "Authorization": f"Bearer {LANGFLOW_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        # Send POST request to Langflow API
        langflow_response = requests.post(langflow_url, json=payload, headers=headers)
        langflow_response.raise_for_status()

        # Parse Langflow's response and return it
        langflow_data = langflow_response.json()
        langflow_message = langflow_data["outputs"][0]["outputs"][0]["outputs"]["message"]["message"]["text"]

        return jsonify({"response": langflow_message})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)