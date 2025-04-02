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

    retriever = vector_store.as_retriever()
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
    )
    logger.info("LLM loaded")
    
    # Create the prompt template for the RetrievalQA chain
    question_prompt = ChatPromptTemplate.from_messages([
        ("system", settings.SYSTEM_PROMPT),
        ("human", "Question: {question}\nContext: {context}")
    ])
    combine_prompt = ChatPromptTemplate.from_messages([
        ("system", settings.SYSTEM_PROMPT),
        ("human", (
            "You are given several partial answers from different pieces of context:\n\n"
            "{summaries}\n\n"
            "Follow these rules {SYSTEM_PROMPT}\n\n"
            "Based on these partial answers, generate a final answer in up to {MAX_GENERATED_SENTENCES} sentences."
        ))
    ])
    combine_prompt = combine_prompt.partial(SYSTEM_PROMPT=settings.SYSTEM_PROMPT)
    combine_prompt = combine_prompt.partial(MAX_GENERATED_SENTENCES=settings.MAX_GENERATED_SENTENCES)
    logger.info("Prompt created")
    
    # Initialize the RetrievalQA chain using the LLM and retriever
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
    
    return RetrievalChainWrapper(chain, cached_embeddings)

async def answer_query(query: str, wrapper: RetrievalChainWrapper) -> str:
    """
    Uses the RetrievalQA chain to generate an answer for a given query.
    """
    answer = await wrapper.chain.ainvoke(query)

    result = answer.get("result")
    logger.info(f"Answer generated: {result}")
    source_docs = answer.get("source_documents", [])
    # Iterate through the source documents and log their metadata and content
    for doc in source_docs:
        # Assume your Document metadata includes "id" and/or "name"
        doc_id = doc.metadata.get("id", "N/A")
        doc_name = doc.metadata.get("name", "N/A")
        logger.info("Document ID: %s, Document Name: %s", doc_id, doc_name)
        logger.info("Document Content: %s", doc.page_content)

    return answer
