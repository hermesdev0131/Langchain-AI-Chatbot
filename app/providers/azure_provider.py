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

    @classmethod
    async def create(cls):
        """
        Async factory method to initialize all chains upon creation.
        """
        instance = cls()
        # Initialize vector store and cached embeddings once
        vector_store, cached_embeddings = await initialize_vector_store_azure()
        # Initialize retrieval chain and store it
        instance.retrieval_chain = await initialize_retrieval_chain_azure(vector_store, cached_embeddings)
        # Initialize ingest chain as a callable (using partial)
        instance.ingest_chain = partial(ingest_chain_func, vector_store=vector_store)
        # Initialize translation chain
        instance.translation_chain = await initialize_translation_chain_azure()
        return instance

    async def initialize_vector_store(self):
        return await initialize_vector_store_azure()

    async def initialize_retrieval_chain(self):
        # This method is kept for compatibility; retrieval_chain is set in create()
        return self.retrieval_chain
    
    async def initialize_ingest_chain(self):
        return self.ingest_chain
    
    async def initialize_translation_chain(self):
        return self.translation_chain
    
    async def answer_query(self, query: str) -> dict:
        # Use the retrieval chain stored on this instance.
        result = await answer(query, self.retrieval_chain)
        return result

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

    async def transcribe_audio(self, file: UploadFile) -> str:
        return await transcribe_azure(self, file)
