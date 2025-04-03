import asyncio
import logging
import datetime
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate
from langchain_milvus import Zilliz
from langchain.docstore.document import Document
from app.config import settings

logger = logging.getLogger(__name__)

class RetrievalChainWrapper:
    """
    A simple wrapper to hold:
      - The RetrievalQA chain (which queries 'innovation_campus')
      - A separate user_queries_vectorstore (which inserts user queries into 'user_queries')
      - The cached embeddings
    """
    def __init__(self, chain, embeddings, user_queries_vectorstore):
        self.chain = chain
        self.embeddings = embeddings
        self.user_queries_vectorstore = user_queries_vectorstore

async def initialize_retrieval_chain(vector_store, cached_embeddings) -> RetrievalChainWrapper:

    # Create a retriever from that store
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})
    logger.info("Retriever created")
    
    # Initialize LLM
    llm = await asyncio.to_thread(
        ChatOpenAI,
        model_name=settings.OPENAI_API_CHAT_MODEL_NAME,
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=settings.TEMPERATURE,
        request_timeout=settings.REQUEST_TIMEOUT
    )
    logger.info("LLM loaded")
    
    # Create prompt
    question_prompt = ChatPromptTemplate.from_messages([
        ("system", settings.SYSTEM_PROMPT),
        ("human", "Question: {question}\nContext: {context}")
    ])
    combine_prompt = ChatPromptTemplate.from_messages([
        ("system", settings.SYSTEM_PROMPT),
        ("human", "You are given several partial answers generated from different pieces of context:\n\n{summaries}\n\nBased on these, please provide a final answer in up to 5 sentences, following the rules above.")
    ])
    logger.info("Prompt created")
    
    # Initialize the RetrievalQA chain
    chain = await asyncio.to_thread(
        RetrievalQA.from_chain_type,
        llm=llm,
        chain_type="map_reduce",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={
            "question_prompt": question_prompt,
            "combine_prompt": combine_prompt,
        }
    )
    logger.info("RetrievalQA chain initialized")
    
    # Also create a separate Zilliz vector store for storing user queries
    user_queries_vectorstore = await asyncio.to_thread(
        Zilliz,
        embedding_function=cached_embeddings,
        collection_name=settings.ZILLIZ_USER_QUERIES_COLLECTION_NAME,
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
        text_field="text",
        vector_field="vector",
        auto_id=True,
        drop_old=False
    )
    logger.info("Connected to Zilliz for user queries insertion")
    
    # Return the wrapper with chain + cached embeddings + user_queries store
    return RetrievalChainWrapper(chain, cached_embeddings, user_queries_vectorstore)

async def answer_and_store(query: str, wrapper: RetrievalChainWrapper) -> str:
    """
    1) Use the wrapper.chain (which retrieves from 'COLLECTION_NAME') to get the answer.
    2) Insert the user's query into the 'user_queries' collection (so we can see them in Zilliz Cloud).
    """

    # Invoke the chain and get a dictionary with keys "result" and "source_documents"
    result = await wrapper.chain.ainvoke(query)
    source_docs = result.get("source_documents", [])
    
    # Optionally, log details of each retrieved document
    for idx, doc in enumerate(source_docs):
        logger.info("Doc %d - Content: %s, Metadata: %s", idx, doc.page_content, doc.metadata)
    
    # Store the user's query in the separate Zilliz vector store
    doc = Document(
        page_content=query,
        metadata={
            "timestamp": int(datetime.datetime.now().timestamp()),
        }
    )
    await asyncio.to_thread(wrapper.user_queries_vectorstore.add_documents, [doc])
    
    return result
