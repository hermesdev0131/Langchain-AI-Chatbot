import aiofiles
import os
import time
import tempfile
import requests
import openai
from dotenv import load_dotenv
from quart import Quart, request, jsonify, Response
from langflow_api import run_flow

# Load environment variables
load_dotenv()
RENDER_LANGFLOW_API_KEY = os.getenv("RENDER_LANGFLOW_API_KEY")
ZILLIZ_AUTH_TOKEN = os.getenv("ZILLIZ_AUTH_TOKEN")
ZILLIZ_URL = "https://in03-30505f4d990015f.serverless.gcp-us-west1.cloud.zilliz.com/v2/vectordb/entities/query"
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Quart(__name__, static_folder='static')

# Serve the static index.html
@app.route('/', methods=['GET'])
async def serve_index():
    file_path = os.path.join(app.static_folder, "index.html")
    try:
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
            content = await f.read()
        return Response(content, mimetype='text/html')
    except FileNotFoundError:
        return Response("index.html not found", status=404)

# Handle POST requests from the front-end
@app.route('/', methods=['POST'])
async def handle_post():
    data = await request.get_json()
    user_message = data.get('userMessage', 'No message provided')

    response = await run_flow(user_message, api_key=RENDER_LANGFLOW_API_KEY)
    return jsonify({"response": response})

# Fetch FAQs from Zilliz
async def query_faqs():
    payload = {
        "collectionName": "faq_collection",
        "outputFields": ["faq"]
    }
    headers = {
        "Authorization": ZILLIZ_AUTH_TOKEN,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    response = requests.post(ZILLIZ_URL, json=payload, headers=headers)
    return response.json()

@app.route('/api/faqs', methods=['GET'])
async def get_faqs():
    data = await query_faqs()
    faqs = [record.get("faq") for record in data.get("data", []) if record.get("faq")]
    return jsonify(faqs)

# Rate limiting & audio file constraints
RATE_LIMIT = 5  # Max requests per minute
RATE_WINDOW = 60  # Rate limit time window (seconds)
user_requests = {}  # Track user IPs
MAX_AUDIO_FILE_SIZE = 2 * 1024 * 1024  # 2MB file limit (~10 seconds audio)

@app.route('/api/transcribe', methods=['POST'])
async def transcribe_audio():
    user_ip = request.remote_addr
    current_time = time.time()
    
    # Apply rate limiting
    request_timestamps = [t for t in user_requests.get(user_ip, []) if current_time - t < RATE_WINDOW]
    if len(request_timestamps) >= RATE_LIMIT:
        return jsonify({"error": "Rate limit exceeded. Try again later."}), 429

    request_timestamps.append(current_time)
    user_requests[user_ip] = request_timestamps

    # Check for uploaded file
    files = await request.files
    if 'file' not in files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = files['file']
    if audio_file.content_length > MAX_AUDIO_FILE_SIZE:
        return jsonify({"error": "Audio file is too large. Please record a shorter clip."}), 400

    try:
        # Save to a temp file
        temp_fd, temp_path = tempfile.mkstemp(suffix=".webm")
        os.close(temp_fd)
        await audio_file.save(temp_path)

        # Transcribe with OpenAI Whisper
        with open(temp_path, "rb") as audio:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio
            )

        os.remove(temp_path)  # Cleanup
        transcript_text = transcript.text if hasattr(transcript, 'text') else transcript.get("text", "")
        return jsonify({"transcript": transcript_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False)