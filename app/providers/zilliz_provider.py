import requests
from .base import BaseProvider
from app.config import settings
from app.chains import *
import logging
from fastapi import UploadFile
from openai import OpenAI
from app.chains.retrieval_chain_zilliz import answer_and_store as answer

logger = logging.getLogger(__name__)

class ZillizProvider(BaseProvider):
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        # These will be set during asynchronous initialization
        self.retrieval_chain = None
        self.ingest_chain = None
        self.translation_chain = None

    @classmethod
    async def create(cls):
        """
        Async factory method to create a fully initialized ZillizProvider instance.
        """
        instance = cls()
        # Initialize vector store and cached embeddings (if applicable)
        vector_store, cached_embeddings = await instance.initialize_vector_store()
        # Initialize and store the retrieval chain
        instance.retrieval_chain = await instance.initialize_retrieval_chain()
        # Initialize and store the ingest chain (placeholder if not implemented)
        instance.ingest_chain = await instance.initialize_ingest_chain()
        # Initialize and store the translation chain
        instance.translation_chain = await instance.initialize_translation_chain()
        return instance

    async def initialize_vector_store(self):
        # Initialize vector store for Zilliz (if applicable)
        # Placeholder: adjust logic as needed for your implementation.
        cached_embeddings = None  
        return None, cached_embeddings

    async def initialize_retrieval_chain(self):
        return await initialize_retrieval_chain_zilliz()
    
    async def initialize_ingest_chain(self):
        # Implement ingest chain initialization for Zilliz, if available.
        # Currently returning None as a placeholder.
        return None
    
    async def initialize_translation_chain(self):
        return await initialize_translation_chain_openai_api()
    
    async def answer_query(self, query):
        return await answer(query, self.retrieval_chain)

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
    
    async def transcribe_audio(self, file: UploadFile) -> str:
        return await transcribe_openai_api(self, file)
