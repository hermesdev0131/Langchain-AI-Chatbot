# app/providers/azure_provider.py
import os
import tempfile
import aiofiles
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from .base import BaseProvider
from app.config import settings
from app.chains import *
from app.chains.ingest_chain_azure import initialize_ingest_chain as ingest_chain_func
import logging
from fastapi import UploadFile
from openai import OpenAI
from functools import partial

logger = logging.getLogger(__name__)

def serialize_document(doc: dict) -> dict:
    if "_id" in doc and isinstance(doc["_id"], ObjectId):
        doc["_id"] = str(doc["_id"])
    return doc

class AzureProvider(BaseProvider):
    def __init__(self):
        self.mongo_client = AsyncIOMotorClient(settings.AZURE_MONGO_CONNECTION_STRING)
        self.db = self.mongo_client[settings.AZURE_MONGO_DATABASE_NAME]
        self.faq_collection = self.db["faq"]
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    async def initialize_vector_store(self):
        return await initialize_vector_store_azure()

    async def initialize_retrieval_chain(self):
        vector_store, cached_embeddings = await self.initialize_vector_store()
        return await initialize_retrieval_chain_azure(vector_store, cached_embeddings)
    
    async def initialize_ingest_chain(self):
        vector_store, _ = await self.initialize_vector_store()  # call the correct method
        ingest_chain_callable = partial(ingest_chain_func, vector_store=vector_store)
        return ingest_chain_callable
    
    async def initialize_translation_chain(self):
        return await initialize_translation_chain()

    async def query_faqs(self) -> dict:
        cursor = self.faq_collection.find({})
        faqs = await cursor.to_list(length=1000)
        serialized_faqs = [serialize_document(faq) for faq in faqs]
        logger.info("serialized_faqs: %s", serialized_faqs)
        transformed = []
        for faq in serialized_faqs:
            faq_content = faq.get("faqs", faq)
            transformed.append({"faq": faq_content})
        return {"data": transformed}

    async def transcribe_audio(self, file: "UploadFile") -> str:
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
