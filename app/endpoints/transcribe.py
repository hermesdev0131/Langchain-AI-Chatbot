import os
import time
import tempfile
import asyncio
import aiofiles
from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

RATE_LIMIT = 5        # Max requests per minute
RATE_WINDOW = 60      # Rate limit time window (seconds)
user_requests = {}    # Track user IPs
MAX_AUDIO_FILE_SIZE = 2 * 1024 * 1024  # 2MB file limit

@router.post("/transcribe")
async def transcribe_audio(request: Request, file: UploadFile = File(...)):
    user_ip = request.client.host
    current_time = time.time()
    request_timestamps = [t for t in user_requests.get(user_ip, []) if current_time - t < RATE_WINDOW]
    if len(request_timestamps) >= RATE_LIMIT:
        logger.warning(f"Rate limit exceeded for IP {user_ip}")
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    request_timestamps.append(current_time)
    user_requests[user_ip] = request_timestamps

    try:
        provider = request.state.provider
        transcript_text = await provider.transcribe_audio(file)
    except Exception as e:
        logger.error(f"Error during transcription: {e}")
        raise HTTPException(status_code=500, detail="Error during transcription")

    return JSONResponse({"transcript": transcript_text})
