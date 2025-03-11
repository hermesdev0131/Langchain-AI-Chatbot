import asyncio
import logging
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate
from langchain_milvus import Zilliz
from app.config import settings

logger = logging.getLogger(__name__)

async def initialize_retrieval_chain() -> RetrievalQA:
    logger.info("Starting chain initialization...")
    # Load embeddings
    embeddings = await asyncio.to_thread(
        OpenAIEmbeddings,
        openai_api_key=settings.OPENAI_API_KEY,
        model="text-embedding-3-large"
    )
    logger.info("Embeddings loaded")
    
    # Connect to Zilliz Cloud
    vectorstore = await asyncio.to_thread(
        Zilliz,
        embedding_function=embeddings,
        collection_name="innovation_campus",
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
        auto_id=True,
        drop_old=False
    )
    logger.info("Connected to Zilliz Cloud")
    
    # Create retriever (fetches top 10 documents)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
    logger.info("Retriever created")
    
    # Initialize LLM
    llm = await asyncio.to_thread(
        ChatOpenAI,
        model_name="gpt-4o-mini",
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=0,
        request_timeout=20_000
    )
    logger.info("LLM loaded")
    
    # Create prompt template with instructions
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            (
                "Please answer the question below in up to 5 sentences (not including any extra links), or give information, following these rules:\n"
                "1. Only use information explicitly contained in the context.\n"
                "2. If the context contains relevant links (for images, videos, or external pages) that relate to any topic, include them exactly as provided.\n"
                "3. Include image, video, and external links related to the question, even if not explicitly requested. Prioritize image and video links.\n"
                "4. Do not fabricate or guess any links that are not in the context.\n"
                "6. If there isn’t enough detail, respond with: \"I do not have enough information from the provided context.\""
            )
        ),
        ("human", "Question: {question}\nContext: {context}")
    ])
    logger.info("Prompt created")
    
    # Initialize RetrievalQA chain (using from_chain_type; note that this API may be deprecated)
    chain = await asyncio.to_thread(
        RetrievalQA.from_chain_type,
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=False,
        chain_type_kwargs={"prompt": prompt}
    )
    logger.info("RetrievalQA chain initialized")
    
    return chain
