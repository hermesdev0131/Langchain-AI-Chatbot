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
from langchain_core.messages import AIMessageChunk
from langchain.docstore.document import Document
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
    
    async def answer_query_stream(self, query: str):
        """Yield tokens from the LLM as they are produced by LangChain using LCEL."""
        
        logger.debug(f"answer_query_stream (LCEL): Initialized for query: '{query}'")

        token_count = 0
        full_response_for_analytics = [] 

        try:
            # The LCEL chain expects the query string directly as input.
            async for chunk in self.retrieval_chain.chain.astream(query):
                # logger.info(f"answer_query_stream (LCEL): RAW chunk received: {chunk!r}") # Can be very verbose

                actual_token = ""
                if isinstance(chunk, AIMessageChunk):
                    actual_token = chunk.content
                elif isinstance(chunk, str): # Should ideally not happen if LLM is the last streaming component
                    actual_token = chunk
                    logger.warning(f"answer_query_stream (LCEL): Received a direct string chunk: '{actual_token}'")
                elif chunk: # If chunk is not empty but not recognized (e.g. a dict from a misconfigured chain)
                    logger.warning(f"answer_query_stream (LCEL): Received chunk of unexpected type or structure: {type(chunk)} - {chunk!r}")
                    # Avoid yielding raw dicts/objects to the client if they are not string content
                
                if actual_token: # Only yield if we have actual string content
                    # logger.info(f"answer_query_stream (LCEL): Yielding processed token: '{actual_token}'") # Verbose
                    token_count += 1
                    full_response_for_analytics.append(actual_token)
                    yield actual_token
                # else:
                    # logger.debug(f"answer_query_stream (LCEL): Empty actual_token from chunk: {chunk!r}")


        except Exception as e:
            logger.error(f"answer_query_stream (LCEL): Error during streaming for query '{query}': {e}", exc_info=True)
            yield f"Error: An error occurred while streaming the response." 
        
        logger.debug(f"answer_query_stream (LCEL): Finished yielding tokens. Total tokens: {token_count} for query: '{query}'")

        # # Analytics insert (non‑blocking background task)
        # doc = Document(page_content=query, metadata={"timestamp": int(time.time())})
        # asyncio.create_task(
        #     asyncio.to_thread(self.retrieval_chain.user_queries_vectorstore.add_documents, [doc])
        # )
        # logger.debug(f"answer_query_stream (LCEL): Analytics task created for query: '{query}'")

    
    async def get_faqs(self) -> list:
        current_time = time.time()
        # Check if the cache exists and is still valid.
        if self._cached_faqs is not None and (current_time - self._cache_timestamp) < self._cache_ttl:
            logger.debug("Using cached FAQs")
            return self._cached_faqs

        logger.debug("Retrieving FAQs from database")
        cursor = self.faq_collection.find({})
        faqs = await cursor.to_list(length=1000) # Adjust length as needed
        serialized_faqs = [serialize_document(faq) for faq in faqs]

        # Process documents: extract heading and subheadings.
        # The database stores "subheadings" (plural), client expects "subheading" (singular).
        faq_list = [
            {
                "heading": item.get("heading"),
                "subheading": item.get("subheadings", []) # Remap "subheadings" to "subheading"
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
        Leverages asyncio.gather for concurrent translation of heading and subheadings.
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
        # This method should ideally query a vector store or search index
        # containing user queries or other relevant data for analytics.
        raise NotImplementedError("search_data is not implemented for AzureProvider.")

    async def delete_document(self, id: str) -> dict:
        """
        Delete a document using the Azure-specific delete functionality.
        """
        try:
            # Note: Successful or not found deletion will return the same message, making it hard to tell if it was really deleted.
            return await delete_document_azure(id)
        except Exception as e:
            logger.error(f"Error deleting document {id}: {e}")
            return {"message": f"Error deleting document: {str(e)}", "status": "error"}

    async def delete_all_documents(self) -> dict:
        """
        Delete all documents using the Azure-specific delete functionality.
        """
        try:
            return await delete_all_documents_azure()
        except Exception as e:
            logger.error(f"Error deleting all documents: {e}")
            return {"message": f"Error deleting all documents: {str(e)}", "status": "error"}
