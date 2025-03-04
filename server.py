import os
import time
import tempfile
import requests
from openai import OpenAI
from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from langflow_api import run_flow
import asyncio
import aiofiles
import uvicorn

# Load environment variables
load_dotenv()
RENDER_LANGFLOW_API_KEY = os.getenv("RENDER_LANGFLOW_API_KEY")
ZILLIZ_AUTH_TOKEN = os.getenv("ZILLIZ_AUTH_TOKEN")
ZILLIZ_URL = os.getenv("ZILLIZ_URL")
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),  # This is the default and can be omitted
)
app = FastAPI()

# Allow CORS for all origins (adjust as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the static files directory
static_folder = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_folder), name="static")

# Serve the static index.html
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    file_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    try:
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
            content = await f.read()
        return HTMLResponse(content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="index.html not found")

# Handle POST requests from the front-end
@app.post("/")
async def handle_post(request: Request):
    data = await request.json()
    user_message = data.get('userMessage', 'No message provided')

    response = await run_flow(user_message, api_key=RENDER_LANGFLOW_API_KEY)
    return JSONResponse({"response": response})

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

@app.get("/api/faqs")
async def get_faqs():
    data = await query_faqs()
    faqs = [record.get("faq") for record in data.get("data", []) if record.get("faq")]
    return JSONResponse(faqs)

async def translate_faq_item(faq, target_lang):
    prompt = f"Translate the following text to {target_lang}:\n\n{faq}\n\n. Do not include anything but the translation"
    try:
        # Run the synchronous call in a separate thread.
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.
        )
        translation = response.choices[0].message.content.strip()
        return translation
    except Exception as e:
        print(f"Translation failed for FAQ: {faq}, error: {e}")
        return faq  # Fallback to original FAQ

@app.get("/api/faqs/translate")
async def translate_faqs(lang: str = 'en'):
    target_lang = lang.lower()
    data = await query_faqs()
    faq_questions = [record.get("faq") for record in data.get("data", []) if record.get("faq")]

    # If target language is English, return original FAQs
    if target_lang == 'en':
        return JSONResponse(faq_questions)

    # Create tasks for all translation requests concurrently.
    tasks = [translate_faq_item(faq, target_lang) for faq in faq_questions]
    translated_faqs = await asyncio.gather(*tasks)
    return JSONResponse(translated_faqs)

# Rate limiting & audio file constraints
RATE_LIMIT = 5  # Max requests per minute
RATE_WINDOW = 60  # Rate limit time window (seconds)
user_requests = {}  # Track user IPs
MAX_AUDIO_FILE_SIZE = 2 * 1024 * 1024  # 2MB file limit (~10 seconds audio)

@app.post("/api/transcribe")
async def transcribe_audio(request: Request, file: UploadFile = File(...)):
    user_ip = request.client.host
    current_time = time.time()

    # Apply rate limiting
    request_timestamps = [t for t in user_requests.get(user_ip, []) if current_time - t < RATE_WINDOW]
    if len(request_timestamps) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

    request_timestamps.append(current_time)
    user_requests[user_ip] = request_timestamps

    # Check for uploaded file size
    contents = await file.read()
    if len(contents) > MAX_AUDIO_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Audio file is too large. Please record a shorter clip.")

    try:
        # Save to a temp file
        temp_fd, temp_path = tempfile.mkstemp(suffix=".webm")
        os.close(temp_fd)
        async with aiofiles.open(temp_path, 'wb') as out_file:
            await out_file.write(contents)

        # Transcribe with OpenAI Whisper
        with open(temp_path, "rb") as audio:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio
            )

        os.remove(temp_path)  # Cleanup
        transcript_text = transcript.text if hasattr(transcript, 'text') else transcript.get("text", "")
        return JSONResponse({"transcript": transcript_text})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    # Only run Uvicorn manually if NOT on Render
    if "RENDER" not in os.environ:
        port = int(os.environ.get("PORT", 8000))  # Default to 8000 for local dev
        print(f"Running locally on port {port}...")
        uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)