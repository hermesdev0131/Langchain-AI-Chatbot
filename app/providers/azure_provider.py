from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from .base import BaseProvider
from app.config import settings
from app.chains import *
import logging
import asyncio
from fastapi import UploadFile
from openai import OpenAI
import time
from app.chains.retrieval_chain_azure import answer_query as answer

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
        # These attributes will be initialized asynchronously
        self.retrieval_chain = None
        self.ingest_chain = None
        self.translation_chain = None
        # Initialize caching variables for FAQs
        self._cached_faqs = None
        self._cache_timestamp = None
        self._cache_ttl = 300  # seconds, e.g., re-fetch every 5 minutes


    @classmethod
    async def create(cls):
        """
        Async factory method to initialize all chains upon creation.
        """
        instance = cls()
        vector_store, cached_embeddings = await initialize_vector_store_azure()
        instance.retrieval_chain = await initialize_retrieval_chain_azure(vector_store, cached_embeddings)
        instance.ingest_chain = await initialize_ingest_chain(vector_store)
        instance.translation_chain = await initialize_translation_chain_azure()
        return instance

    async def answer_query(self, query: str) -> dict:
        return await answer(query, self.retrieval_chain)

    async def get_faqs(self) -> list:
        current_time = time.time()
        # Check if the cache exists and is still valid.
        if self._cached_faqs is not None and (current_time - self._cache_timestamp) < self._cache_ttl:
            logger.info("Using cached FAQs")
            return self._cached_faqs

        logger.info("Retrieving FAQs from database")
        cursor = self.faq_collection.find({})
        faqs = await cursor.to_list(length=1000)
        serialized_faqs = [serialize_document(faq) for faq in faqs]

        # Fix: Use "subheadings" from DB and remap it to "subheading"
        faq_list = [
            {
                "heading": item.get("heading"),
                "subheading": item.get("subheadings", [])
            }
            for doc in serialized_faqs
            for item in doc.get("faqs", [])
            if isinstance(item, dict) and item.get("heading")
        ]
        # Update cache and timestamp.
        self._cached_faqs = faq_list
        self._cache_timestamp = current_time
        return faq_list

    async def translate_faqs(self, target_lang: str = 'en') -> list:
        """
        Translates FAQs to the target language using the translation chain.
        If target language is English, returns cached FAQs.
        """
        faq_texts = await self.get_faqs()  # This now uses caching with TTL
        if target_lang.lower() == 'en':
            return faq_texts

        translated_faqs = []

        for faq in faq_texts:
            heading_task = asyncio.to_thread(
                self.translation_chain.invoke,
                {"faq": faq["heading"], "target_lang": target_lang}
            )

            subheading_tasks = [
                asyncio.to_thread(
                    self.translation_chain.invoke,
                    {"faq": sub, "target_lang": target_lang}
                ) for sub in faq.get("subheading", [])
            ]

            results = await asyncio.gather(heading_task, *subheading_tasks)
            heading_result = results[0]
            subheading_results = results[1:]

            translated_faqs.append({
                "heading": heading_result.content if hasattr(heading_result, "content") else str(heading_result),
                "subheading": [
                    r.content if hasattr(r, "content") else str(r)
                    for r in subheading_results
                ]
            })

        return translated_faqs

    async def transcribe_audio(self, file: UploadFile) -> str:
        return await transcribe_azure(self, file)

    async def search_data(self, query: str, limit: int = 100, radius: float = 0.8) -> dict:
        # TODO: Implement data analytics search functionality for AzureProvider.
        raise NotImplementedError("search_data is not implemented for AzureProvider.")
