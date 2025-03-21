# providers/zilliz_provider.py
import requests
from .base import BaseProvider
from app.config import settings
from app.chains import *
import logging
from fastapi import UploadFile
import aiofiles
import tempfile
import os
from openai import OpenAI

logger = logging.getLogger(__name__)

class ZillizProvider(BaseProvider):
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    async def initialize_vector_store(self):
        # Initialize vector store for Zilliz (if applicable)
        cached_embeddings = None  # Placeholder
        # Your initialization logic here
        return None, cached_embeddings

    async def initialize_retrieval_chain(self):
        return initialize_retrieval_chain_zilliz
    
    async def initialize_ingest_chain(self):
        return await initialize_ingest_chain()
    
    async def initialize_translation_chain(self):
        return await initialize_translation_chain()

    async def query_faqs(self) -> dict:
        payload = {
            "collectionName": "faq_collection",
            "outputFields": ["faq"]
        }
        headers = {
            "Authorization": f"Bearer {settings.ZILLIZ_AUTH_TOKEN}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        response = requests.post(settings.ZILLIZ_URL + "/v2/vectordb/entities/query", json=payload, headers=headers)
        
        return response.json()
    
    async def transcribe_audio(self, file: "UploadFile") -> str:
        # For demonstration, assume Zilliz provider uses the same transcription logic.
        # Otherwise, adjust this method accordingly.
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
                logger.info("Sending audio file for transcription (Zilliz)")
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio
                )
                logger.info("Transcription response received (Zilliz)")
        except Exception as e:
            logger.error(f"Error during transcription (Zilliz): {e}")
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
