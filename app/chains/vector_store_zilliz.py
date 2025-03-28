from langchain.embeddings import CacheBackedEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain.storage import InMemoryByteStore
from langchain.vectorstores import Zilliz
import asyncio
from app.config import settings
import logging

logger = logging.getLogger(__name__)

async def initialize_vector_store_zilliz():
    embeddings = OpenAIEmbeddings(
        openai_api_key = settings.OPENAI_API_KEY,
        model = settings.OPENAI_API_EMBEDDING_MODEL_NAME
    )

    # 2. Set up an in-memory byte store and create a cached embeddings function
    byte_store = InMemoryByteStore()
    cached_embeddings = CacheBackedEmbeddings(embeddings, byte_store)
    logger.info("Cached embeddings initialized")

    # 3. Create an Azure AI Search vector store (index) for retrieval
    #    Ensure that your index on Azure is created with the expected schema (e.g., with a "content" field and a "content_vector" field).
    vector_store = await asyncio.to_thread(
        Zilliz,
        embedding_function=cached_embeddings,
        collection_name=settings.ZILLIZ_COLLECTION_NAME,  # <--- queries happen here
        connection_args={
            "uri": settings.ZILLIZ_URL,
            "token": settings.ZILLIZ_AUTH_TOKEN,
        },
        index_params={
            "metric_type": "COSINE",
            "index_type": "HNSW",
            "params": {"M": 8, "efConstruction": 64}
        },
        search_params={
            "metric_type": "COSINE",
            "params": {"ef": 10}
        },
        vector_field=settings.ZILLIZ_VECTOR_FIELD_NAME,
        text_field=settings.ZILLIZ_VECTOR_TEXT_FIELD_NAME,
        auto_id=True,
        drop_old=False
    )

    return vector_store, cached_embeddings