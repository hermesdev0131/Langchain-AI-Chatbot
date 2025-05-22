import asyncio
import logging
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from app.config import settings
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

class RetrievalChainWrapper:
    """
    Wrapper to hold:
      - The RetrievalQA chain (which queries our Azure AI Search index)
      - The cached embeddings
    """
    def __init__(self, chain, embeddings):
        self.chain = chain
        self.embeddings = embeddings

async def initialize_retrieval_chain(vector_store, cached_embeddings) -> RetrievalChainWrapper:
    logger.info("Starting chain initialization...")

    retriever = vector_store.as_retriever(
        search_type="hybrid",
        k=4,
    )

    logger.info("Retriever created")
    
    # Initialize the LLM (using Azure OpenAI via ChatOpenAI)
    llm = await asyncio.to_thread(
        AzureChatOpenAI,
        model_name =        settings.AZURE_MODEL_NAME,
        azure_deployment =  settings.AZURE_DEPLOYMENT_NAME,
        azure_endpoint =    settings.AZURE_OPENAI_ENDPOINT,
        api_key =           settings.AZURE_OPENAI_API_KEY,
        temperature =       settings.TEMPERATURE,
        request_timeout =   settings.REQUEST_TIMEOUT,
        api_version =       settings.AZURE_API_VERSION,
        streaming =         True,
    )
    logger.info("LLM loaded")
    
    # Create the prompt template for the LCEL chain
    question_prompt = ChatPromptTemplate.from_messages([
        ("system", settings.SYSTEM_PROMPT),
        ("human", "Context: {context}\n\nQuestion: {question}\n\nAnswer:")
    ])
    logger.info("Prompt created")

    def format_docs(docs):
        """Helper function to format retrieved documents into a single string."""
        return "\n\n".join(doc.page_content for doc in docs)

    # Initialize the LCEL chain
    lcel_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | question_prompt
        | llm
    )
    logger.info("LCEL RAG chain initialized")
    
    return RetrievalChainWrapper(lcel_chain, cached_embeddings)

async def answer_query(query: str, wrapper: RetrievalChainWrapper) -> dict:
    """
    Uses the LCEL chain from the wrapper to generate an answer for a given query.
    Appends StrOutputParser to get a non-streaming string answer.
    """
    # For a non-streaming response, append StrOutputParser to the LCEL chain
    chain_for_full_answer = wrapper.chain | StrOutputParser()

    logger.debug(f"answer_query: Invoking LCEL chain for full answer with query: {query}")
    result_content = await chain_for_full_answer.ainvoke(query)
    logger.debug(f"Answer generated (first 200 chars): {result_content[:200]}...")

    # Source documents are not directly available from this LCEL chain structure when piped to StrOutputParser.
    # Returning an empty list for consistency with the Zilliz example's answer_and_store output.
    return {"result": result_content, "source_documents": []}
