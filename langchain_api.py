import asyncio
import logging
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate
from langchain_milvus import Zilliz
from config import Settings

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def initialize_chain() -> RetrievalQA:
    """
    Asynchronously connects to Zilliz Cloud and initializes the RetrievalQA chain.
    
    Returns:
        RetrievalQA: The initialized RetrievalQA chain.
    """
    settings = Settings()
    logger.info("Starting chain initialization...")

    # Load embeddings
    try:
        embeddings = await asyncio.to_thread(
            OpenAIEmbeddings,
            openai_api_key=settings.OPENAI_API_KEY,
            model="text-embedding-3-large"
        )
        logger.info("Embeddings loaded")
    except Exception as e:
        logger.error("Error loading embeddings: %s", e)
        raise

    # Connect to Zilliz Cloud
    try:
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
    except Exception as e:
        logger.error("Error connecting to Zilliz Cloud: %s", e)
        raise

    # Create retriever
    try:
        retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
        logger.info("Retriever created")
    except Exception as e:
        logger.error("Error creating retriever: %s", e)
        raise

    # Initialize LLM
    try:
        llm = await asyncio.to_thread(
            ChatOpenAI,
            model_name="gpt-4o-mini",
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0,
            request_timeout=20_000
        )
        logger.info("LLM loaded")
    except Exception as e:
        logger.error("Error initializing LLM: %s", e)
        raise

    # Create prompt
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "Please answer the question below in up to 5 sentences (not including any extra links), or give information, following these rules:\n"
                "1. Only use information explicitly contained in the context.\n"
                "2. If the context contains relevant links (for images, videos, or external pages) that relate to any topic, concept, or entity mentioned in the question, include them exactly as provided.\n"
                "3. Include image, video, and external links related to the question, even if the question does not explicitly request them. Prioritize image and video links.\n"
                "4. Do not fabricate or guess any links that are not present in the context.\n"
                "6. If the context does not provide enough details to answer, respond with: \"I do not have enough information from the provided context.\""
            )),
            ("human", "Question: {question}\nContext: {context}")
        ])
        logger.info("Prompt created")
    except Exception as e:
        logger.error("Error creating prompt: %s", e)
        raise

    # Initialize RetrievalQA chain
    try:
        chain = await asyncio.to_thread(
            RetrievalQA.from_chain_type,
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=False,
            chain_type_kwargs={"prompt": prompt}
        )
        logger.info("RetrievalQA chain initialized")
    except Exception as e:
        logger.error("Error initializing RetrievalQA chain: %s", e)
        raise

    return chain