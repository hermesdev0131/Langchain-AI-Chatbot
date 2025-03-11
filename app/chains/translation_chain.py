import asyncio
import logging
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from app.config import settings

logger = logging.getLogger(__name__)

async def initialize_translation_chain() -> LLMChain:
    """
    Initializes an LLMChain dedicated for translating text.
    """
    logger.info("Starting translation chain initialization...")
    
    # Initialize LLM for translation (can be same or different as needed)
    llm = await asyncio.to_thread(
        ChatOpenAI,
        model_name="gpt-4o-mini",
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=0,
        request_timeout=20_000
    )
    logger.info("LLM loaded for translation")
    
    # Create prompt template for translation
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "Translate the following text to {target_lang}. Provide only the translation."
        ),
        ("human", "{faq}")
    ])
    logger.info("Prompt created for translation chain")
    
    # Create the translation chain using LLMChain
    translation_chain = LLMChain(llm=llm, prompt=prompt)
    logger.info("Translation chain initialized")
    
    return translation_chain