import requests
from .base import BaseProvider
from app.config import settings
from app.chains import *
import logging
import asyncio
import pandas as pd
import time
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
        # Initialize caching variables for FAQs
        self._cached_faqs = None
        self._cache_timestamp = None
        self._cache_ttl = 300  # Time-to-live in seconds (e.g., 5 minutes)


    @classmethod
    async def create(cls):
        """
        Async factory method to initialize all chains upon creation.
        """
        instance = cls()
        vector_store, cached_embeddings = await initialize_vector_store_zilliz()
        instance.retrieval_chain = await initialize_retrieval_chain_zilliz(vector_store, cached_embeddings)
        instance.ingest_chain = await initialize_ingest_chain(vector_store)
        instance.translation_chain = await initialize_translation_chain_openai_api()
        return instance


    async def answer_query(self, query):
        return await answer(query, self.retrieval_chain)


    async def get_faqs(self) -> list:
        current_time = time.time()
        # Check if the cache exists and is still valid.
        if self._cached_faqs is not None and (current_time - self._cache_timestamp) < self._cache_ttl:
            return self._cached_faqs

        logger.info("Retrieving from database")
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
        result = response.json()
        faq_list = [item["faq"] for item in result.get("data", []) if "faq" in item]
        
        # Cache the result and update the timestamp
        self._cached_faqs = faq_list
        self._cache_timestamp = current_time

        return faq_list


    async def translate_faqs(self, target_lang: str = 'en') -> list:
        """
        Translates FAQs to the target language using the translation chain.
        If target language is English, returns FAQs as is.
        """
        faq_texts = await self.get_faqs()
        if target_lang.lower() == 'en':
            return faq_texts

        tasks = [
            asyncio.to_thread(self.translation_chain.invoke, {"faq": faq, "target_lang": target_lang})
            for faq in faq_texts
        ]
        results = await asyncio.gather(*tasks)
        translated_faqs = [result.content if hasattr(result, "content") else str(result) for result in results]
        # Currently not storing translated faqs in cache. Only en faqs
        # Would make sense to store faqs in cache at server startup and periodicalliy update them instead of at chatbot open request
        #   For larger user base this would significantly decrease request count
        #   For smaller and infrequent usage user base, would significantly increase request count
        #   Consider a toggleable option for this

        return translated_faqs

    
    async def transcribe_audio(self, file: UploadFile) -> str:
        return await transcribe_openai_api(self, file)


    async def search_data(self, query: str, limit: int = 100, radius: float = 0.8) -> dict:
        """
        Generates an embedding for the query, searches the user_queries collection in Zilliz,
        and aggregates the results by hour.
        """
        # 1. Generate embedding
        try:
            logger.info("Generating embedding for query: %s", query)
            embedding_response = await asyncio.to_thread(
                self.client.embeddings.create,
                input=query,
                model=settings.OPENAI_API_EMBEDDING_MODEL_NAME
            )
            query_vector = embedding_response.data[0].embedding
            logger.debug("Embedding generated successfully: %s", query_vector[:10])  # partial logging for brevity
        except Exception as e:
            logger.exception("Embedding generation failed")
            raise RuntimeError(f"Embedding generation failed: {e}")

        # 2. Build payload for Zilliz search
        payload = {
            "collectionName": settings.ZILLIZ_USER_QUERIES_COLLECTION_NAME,
            "data": [query_vector],
            "annsField": "vector",
            "limit": limit,
            "searchParams": {
                "metric_type": "COSINE",
                "params": {"nprobe": 10, "radius": radius}
            },
            "outputFields": ["pk", "timestamp"]
        }
        logger.debug("Payload for vectordb search: %s", payload)

        headers = {
            "Authorization": f"Bearer {settings.ZILLIZ_AUTH_TOKEN}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        # 3. Query Zilliz
        try:
            search_url = f"{settings.ZILLIZ_URL}/v2/vectordb/entities/search"
            logger.info("Sending request to Zilliz URL: %s", search_url)
            response = requests.post(search_url, json=payload, headers=headers)
            response.raise_for_status()
            logger.debug("Response status code: %s", response.status_code)
            result = response.json()
            logger.debug("Response JSON: %s", result)

            # 4. Convert response data to a DataFrame
            data = result.get("data", [])
            df = pd.DataFrame(data)
            if df.empty or "timestamp" not in df.columns:
                logger.warning("No data found or missing 'timestamp' field in response")
                return {"frequency": 0, "result": []}
            
            # 5. Group by hour and compute frequency
            df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")
            grouped = (
                df.groupby(df["datetime"].dt.floor("h"))
                  .size()
                  .reset_index(name="frequency")
            )
            grouped.sort_values(by="datetime", inplace=True)
            grouped["datetime"] = grouped["datetime"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            aggregated_results = grouped.to_dict(orient="records")
            total_frequency = int(grouped["frequency"].sum())
            logger.info("Successfully aggregated data with total frequency: %d", total_frequency)
        except Exception as e:
            logger.exception("Zilliz query failed")
            raise RuntimeError(f"Zilliz query failed: {e}")

        return {"frequency": total_frequency, "result": aggregated_results}