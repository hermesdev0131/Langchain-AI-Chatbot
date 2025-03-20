import asyncio
import logging
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from app.config import settings

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
    
    
    # 4. Create a retriever from the vector store
    retriever = vector_store.as_retriever()
    logger.info("Retriever created")
    
    # 5. Initialize the LLM (using Azure OpenAI via ChatOpenAI)
    llm = await asyncio.to_thread(
        AzureChatOpenAI,
        model_name =        settings.AZURE_MODEL_NAME,
        azure_deployment =  settings.AZURE_DEPLOYMENT_NAME,
        azure_endpoint =    settings.AZURE_OPENAI_ENDPOINT,  # e.g., "https://your-resource-name.openai.azure.com/"
        api_key =           settings.AZURE_OPENAI_API_KEY,
        temperature =       settings.TEMPERATURE,
        request_timeout =   settings.REQUEST_TIMEOUT,
        api_version =       settings.AZURE_API_VERSION,
    )
    logger.info("LLM loaded")
    
    # 6. Create the prompt template for the RetrievalQA chain
    prompt = ChatPromptTemplate.from_messages([
        ("system", settings.SYSTEM_PROMPT),
        ("human", "Question: {question}\nContext: {context}")
    ])
    logger.info("Prompt created")
    
    # 7. Initialize the RetrievalQA chain using the LLM and retriever
    chain = await asyncio.to_thread(
        RetrievalQA.from_chain_type,
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=False,
        chain_type_kwargs={"prompt": prompt}
    )
    logger.info("RetrievalQA chain initialized")
    
    return RetrievalChainWrapper(chain, cached_embeddings)

async def answer_query(query: str, wrapper: RetrievalChainWrapper) -> str:
    """
    Uses the RetrievalQA chain to generate an answer for a given query.
    """
    answer = await wrapper.chain.ainvoke(query)
    return answer
