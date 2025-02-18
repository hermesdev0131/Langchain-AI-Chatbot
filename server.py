import aiofiles
from quart import Quart, request, jsonify, Response
import os
from dotenv import load_dotenv
from langflow_api import run_flow
import numpy as np
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uvicorn
import openai
import tempfile
from limits.storage import MemoryStorage
from limits.strategies import FixedWindowRateLimiter
import time

load_dotenv()
RENDER_LANGFLOW_API_KEY = os.getenv("RENDER_LANGFLOW_API_KEY")
ZILLIZ_AUTH_TOKEN = os.getenv("ZILLIZ_AUTH_TOKEN")
ZILLIZ_URL = "https://in03-30505f4d990015f.serverless.gcp-us-west1.cloud.zilliz.com/v2/vectordb/entities/query"
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Quart(__name__, static_folder='static')
executor = ThreadPoolExecutor()

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

def query_faqs():
    """
    Synchronous function that queries the FAQ collection from Zilliz.
    Adjust the payload structure as required by your collection schema.
    """
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

# Rate limiting settings
storage = MemoryStorage()  # Uses in-memory storage for limits
rate_limiter = FixedWindowRateLimiter(storage)
RATE_LIMIT = 5  # Max requests allowed
RATE_WINDOW = 60  # Time window in seconds (5 per minute)
# Track request timestamps per user (IP-based)
user_requests = {}
MAX_AUDIO_FILE_SIZE = 2 * 1024 * 1024  # 2MB file size limit (approx 10s audio)

@app.route('/api/transcribe', methods=['POST'])
async def transcribe_audio():
    user_ip = request.remote_addr  # Get user IP

    # Rate limiting logic
    current_time = time.time()
    request_timestamps = user_requests.get(user_ip, [])
    request_timestamps = [t for t in request_timestamps if current_time - t < RATE_WINDOW]

    if len(request_timestamps) >= RATE_LIMIT:
        return jsonify({"error": "Rate limit exceeded. Try again later."}), 429

    request_timestamps.append(current_time)
    user_requests[user_ip] = request_timestamps

    files = await request.files
    if 'file' not in files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = files['file']

    if audio_file.content_length > MAX_AUDIO_FILE_SIZE:
        return jsonify({"error": "Audio file is too large. Please record a shorter clip."}), 400

    try:
        temp_fd, temp_path = tempfile.mkstemp(suffix=".webm")
        os.close(temp_fd)
        await audio_file.save(temp_path)

        with open(temp_path, "rb") as audio:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio
            )

        os.remove(temp_path)
        transcript_text = transcript.text if hasattr(transcript, 'text') else transcript.get("text", "")

        return jsonify({"transcript": transcript.text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/faqs', methods=['GET'])
async def get_faqs():
    """
    Asynchronously retrieves FAQs by offloading the blocking query
    to a thread pool.
    """
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(executor, query_faqs)

    faqs = []
    if "data" in data:
        for record in data["data"]:
            faq = record.get("faq")
            if faq:
                faqs.append(faq)
    return jsonify(faqs)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))

    # Run Uvicorn only if not running inside Render (which starts it automatically)
    if "RENDER" not in os.environ:
        print(f"Running locally on port {port}...")
        uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)