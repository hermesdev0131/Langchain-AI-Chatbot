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
    
    # Rate limiting
    request_timestamps = [t for t in user_requests.get(user_ip, []) if current_time - t < RATE_WINDOW]
    if len(request_timestamps) >= RATE_LIMIT:
        logger.warning(f"Rate limit exceeded for IP {user_ip}")
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    request_timestamps.append(current_time)
    user_requests[user_ip] = request_timestamps
    
    try:
        contents = await file.read()
        logger.info(f"Received file of size {len(contents)} bytes from {user_ip}")
    except Exception as e:
        logger.error(f"Error reading uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Error reading file")
    
    if len(contents) > MAX_AUDIO_FILE_SIZE:
        logger.warning(f"File too large: {len(contents)} bytes")
        raise HTTPException(status_code=400, detail="Audio file is too large. Please record a shorter clip.")
    
    try:
        temp_fd, temp_path = tempfile.mkstemp(suffix=".webm")
        os.close(temp_fd)
        logger.info(f"Temporary file created at {temp_path}")
    except Exception as e:
        logger.error(f"Error creating temporary file: {e}")
        raise HTTPException(status_code=500, detail="Error creating temporary file")
    
    try:
        async with aiofiles.open(temp_path, 'wb') as out_file:
            await out_file.write(contents)
        logger.info(f"Wrote uploaded file to temporary file {temp_path}")
    except Exception as e:
        logger.error(f"Error writing to temporary file: {e}")
        raise HTTPException(status_code=500, detail="Error writing file")
    
    try:
        with open(temp_path, "rb") as audio:
            logger.info("Sending audio file for transcription using settings.client")
            transcript = settings.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio
            )
            logger.info("Transcription response received")
    except Exception as e:
        logger.error(f"Error during transcription: {e}")
        raise HTTPException(status_code=500, detail="Error during transcription")
    finally:
        try:
            os.remove(temp_path)
            logger.info(f"Temporary file {temp_path} removed")
        except Exception as e:
            logger.warning(f"Failed to remove temporary file {temp_path}: {e}")
    
    try:
        transcript_text = transcript.text if hasattr(transcript, 'text') else transcript.get("text", "")
        logger.info(f"Transcription text (first 50 chars): {transcript_text[:50]}...")
    except Exception as e:
        logger.error(f"Error extracting transcription text: {e}")
        raise HTTPException(status_code=500, detail="Error processing transcription response")
    
    return JSONResponse({"transcript": transcript_text})
