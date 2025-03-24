import os
import tempfile
import aiofiles
from fastapi import UploadFile
import logging

logger = logging.getLogger(__name__)

async def transcribe(self, file: "UploadFile") -> str:
    # Read the uploaded file (assumes file is of type UploadFile)
    try:
        contents = await file.read()
        logger.info(f"Received audio file of size {len(contents)} bytes")
    except Exception as e:
        logger.error(f"Error reading uploaded file: {e}")
        raise e

    MAX_AUDIO_FILE_SIZE = 2 * 1024 * 1024  # 2MB
    if len(contents) > MAX_AUDIO_FILE_SIZE:
        raise ValueError("Audio file is too large. Please record a shorter clip.")

    try:
        temp_fd, temp_path = tempfile.mkstemp(suffix=".webm")
        os.close(temp_fd)
        logger.info(f"Temporary file created at {temp_path}")
    except Exception as e:
        logger.error(f"Error creating temporary file: {e}")
        raise e

    try:
        async with aiofiles.open(temp_path, 'wb') as out_file:
            await out_file.write(contents)
        logger.info(f"Wrote audio to temporary file {temp_path}")
    except Exception as e:
        logger.error(f"Error writing to temporary file: {e}")
        raise e

    try:
        with open(temp_path, "rb") as audio:
            logger.info("Sending audio file for transcription")
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio
            )
            logger.info("Transcription response received")
    except Exception as e:
        logger.error(f"Error during transcription: {e}")
        raise e
    finally:
        try:
            os.remove(temp_path)
            logger.info(f"Temporary file {temp_path} removed")
        except Exception as e:
            logger.warning(f"Failed to remove temporary file {temp_path}: {e}")

    try:
        transcript_text = transcript.text if hasattr(transcript, 'text') else transcript.get("text", "")
        logger.info(f"Transcription text (first 50 chars): {transcript_text[:50]}...")
        return transcript_text
    except Exception as e:
        logger.error(f"Error processing transcription response: {e}")
        raise e