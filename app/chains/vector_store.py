from langchain.embeddings import CacheBackedEmbeddings
from langchain_openai import AzureOpenAIEmbeddings
from langchain.storage import InMemoryByteStore
from langchain_community.vectorstores import AzureSearch
import asyncio
from app.config import settings
import logging

logger = logging.getLogger(__name__)

async def initialize_vector_store_azure():
    # 1. Create the underlying embeddings model using Azure OpenAI
    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,  
        deployment=settings.OPENAI_API_EMBEDDING_MODEL_NAME,
    )

    # 2. Set up an in-memory byte store and create a cached embeddings function
    byte_store = InMemoryByteStore()
    cached_embeddings = CacheBackedEmbeddings(embeddings, byte_store)
    logger.info("Cached embeddings initialized")

    # 3. Create an Azure AI Search vector store (index) for retrieval
    #    Ensure that your index on Azure is created with the expected schema (e.g., with a "content" field and a "content_vector" field).
    vector_store = await asyncio.to_thread(
        AzureSearch,
        azure_search_endpoint=settings.AZURE_AI_SEARCH_ENDPOINT,
        azure_search_key=settings.AZURE_AI_SEARCH_API_KEY,
        index_name=settings.AZURE_INDEX_NAME,
        embedding_function=cached_embeddings.embed_query,
    )

    return vector_store, cached_embeddings