import os
import time
import tempfile
import requests
from openai import OpenAI
from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from langflow_api import run_flow
import asyncio
import aiofiles
import uvicorn
import pandas as pd

from config import Settings

# Instantiate the settings
settings = Settings()

# Use the configuration for the OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)

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

    response = await run_flow(user_message, api_key=settings.RENDER_LANGFLOW_API_KEY)
    return JSONResponse({"response": response})

@app.get("/api/search_data")
async def search_data(query: str, limit: int = 100, radius: float = 0.8):
    collection_name = "user_queries"
    model_name = "text-embedding-3-large"

    try:
        embedding_response = await asyncio.to_thread(
            client.embeddings.create, input=query, model=model_name
        )
        # logging.debug("Embedding response: %s", embedding_response)
        # Access the embedding using dot notation
        query_vector = embedding_response.data[0].embedding
    except Exception as e:
        print("Error generating embedding: %s", str(e))
        raise HTTPException(status_code=500, detail="Embedding generation failed: " + str(e))

    payload = {
        "collectionName": collection_name,
        "data": [ query_vector],
        "annsField": "vector",
        "limit": limit,
        "searchParams": {
            "metric_type": "COSINE",
            # nprobe - higher values are more accurate but slower
            # radius - maximum distance for a result to be considered a match
            "params": {"nprobe": 10, "radius": radius}
        },
        "outputFields": ["pk", "timestamp"]
    }
    
    headers = {
        "Authorization": f"Bearer {settings.ZILLIZ_AUTH_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(settings.ZILLIZ_URL + "/search", json=payload, headers=headers)
        response.raise_for_status()  # This will raise an exception for HTTP error codes.
        result = response.json()

        # raw_result is expected to have a structure like:
        # {'code': 0, 'cost': 6, 'data': [ { 'timestamp': 1741132395, ... }, ... ] }
        data = result.get("data", [])
        
        # Convert data into a Pandas DataFrame
        df = pd.DataFrame(data)
        if df.empty or "timestamp" not in df.columns:
            return JSONResponse({
                "frequency": 0,
                "result": []
            })
        
        # Convert timestamp (in seconds) to datetime
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")
        
        # Group by a time interval.
        # For example, group by minute using .dt.floor('T').
        # You can change 'T' to 'H' for hourly or 'D' for daily.
        grouped = df.groupby(df["datetime"].dt.floor("H")).size().reset_index(name="frequency")
        grouped.sort_values(by="datetime", inplace=True)

        # Convert the datetime to a string format
        grouped["datetime"] = grouped["datetime"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Convert to list of dicts for JSONResponse
        aggregated_results = grouped.to_dict(orient="records")
        total_frequency = int(grouped["frequency"].sum())
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Zilliz query failed: " + str(e))
    
    return JSONResponse({
        "frequency": total_frequency,
        "result": aggregated_results
    })

# Fetch FAQs from Zilliz
async def query_faqs():
    payload = {
        "collectionName": "faq_collection",
        "outputFields": ["faq"]
    }
    headers = {
        "Authorization": f"Bearer {settings.ZILLIZ_AUTH_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    response = requests.post(settings.ZILLIZ_URL + "/query", json=payload, headers=headers)
    print(response)
    return response.json()

@app.get("/api/faqs")
async def get_faqs():
    data = await query_faqs()
    faqs = [record.get("faq") for record in data.get("data", []) if record.get("faq")]
    return JSONResponse(faqs)

async def translate_faq_item(faq, target_lang):
    prompt = f"Translate the following text to {target_lang}:\n\n{faq}\n\n. Do not include anything but the translation"
    try:
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
        print(f"Running locally on port {settings.PORT}...")
        uvicorn.run("server:app", host="0.0.0.0", port=settings.PORT, reload=True)
