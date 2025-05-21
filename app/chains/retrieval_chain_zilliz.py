import asyncio
import logging
import datetime
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Zilliz
from langchain.docstore.document import Document
from app.config import settings
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

class RetrievalChainWrapper:
    """
    A simple wrapper to hold:
      - The LCEL chain
      - A separate user_queries_vectorstore
      - The cached embeddings
    """
    def __init__(self, chain, embeddings, user_queries_vectorstore):
        self.chain = chain # This will be an LCEL chain
        self.embeddings = embeddings
        self.user_queries_vectorstore = user_queries_vectorstore

async def initialize_retrieval_chain(vector_store, cached_embeddings) -> RetrievalChainWrapper:
    """Initializes and returns a RetrievalChainWrapper with an LCEL chain for Zilliz."""

    retriever = vector_store.as_retriever(
        search_kwargs={"k": 4} # Retrieve top 4 relevant documents
    )
    logger.debug("Retriever created")
    
    llm = ChatOpenAI(
        model_name=settings.OPENAI_API_CHAT_MODEL_NAME,
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=settings.TEMPERATURE,
        request_timeout=settings.REQUEST_TIMEOUT,
        streaming=True 
    )
    logger.debug("LLM loaded")
    
    # LCEL Prompt using from_messages for system and human roles
    prompt = ChatPromptTemplate.from_messages([
        ("system", settings.SYSTEM_PROMPT), 
        ("human", "Context: {context}\n\nQuestion: {question}\n\nAnswer:")
    ])
    logger.debug("Prompt created for LCEL chain using system and human messages.")
    
    def format_docs(docs):
        """Helper function to format retrieved documents into a single string."""
        return "\n\n".join(doc.page_content for doc in docs)

    # LCEL Chain for streaming:
    # 1. Retrieve context using the retriever and format it.
    # 2. Pass the original question through.
    # 3. Combine context and question into the prompt.
    # 4. Send to LLM for generation.
    lcel_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm # Outputs AIMessageChunk objects when streamed
    )
    logger.debug("LCEL RAG chain initialized for streaming")
    
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
    logger.debug("Connected to Zilliz for user queries insertion")
    
    return RetrievalChainWrapper(lcel_chain, cached_embeddings, user_queries_vectorstore)

async def answer_and_store(query: str, wrapper: RetrievalChainWrapper) -> dict:
    """
    1) Uses the LCEL chain from the wrapper to get a non-streaming answer.
    2) Stores the user's query into the 'user_queries' Zilliz collection for analytics.
    Returns a dictionary with the answer and an empty list for source_documents (as LCEL stream doesn't directly provide them here).
    """
    # For a non-streaming response, append StrOutputParser to the LCEL chain
    chain_for_full_answer = wrapper.chain | StrOutputParser()
    
    logger.debug(f"answer_and_store: Invoking LCEL chain for full answer with query: {query}")
    result_content = await chain_for_full_answer.ainvoke(query)
    logger.debug(f"answer_and_store: Full answer received (first 200 chars): {result_content[:200]}...")
    
    # Store the user's query in the background
    doc = Document(
        page_content=query,
        metadata={
            "timestamp": int(datetime.datetime.now().timestamp()),
        }
    )
    asyncio.create_task(asyncio.to_thread(wrapper.user_queries_vectorstore.add_documents, [doc]))
    
    # Mimic previous output structure if necessary, though source_documents are not directly part of this simple LCEL answer stream
    return {"result": result_content, "source_documents": []}
