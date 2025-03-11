from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import logging
import requests
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

async def query_faqs():
    payload = {
        "collectionName": "faq_collection",
        "outputFields": ["faq"]
    }
    headers = {
        "Authorization": f"Bearer {settings.ZILLIZ_AUTH_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    response = requests.post(settings.ZILLIZ_URL + "/v2/vectordb/entities/query", json=payload, headers=headers)
    return response.json()

@router.get("/faqs")
async def get_faqs():
    data = await query_faqs()
    faqs = [record.get("faq") for record in data.get("data", []) if record.get("faq")]
    return JSONResponse(faqs)

@router.get("/faqs/translate")
async def translate_faqs(request: Request, lang: str = 'en'):
    logger.info(f"Translating FAQs to {lang}")
    target_lang = lang.lower()
    data = await query_faqs()
    faq_questions = [record.get("faq") for record in data.get("data", []) if record.get("faq")]

    # If target language is English, return the original FAQs
    if target_lang == 'en':
        return JSONResponse(faq_questions)

    # Retrieve the translation chain from app state
    try:
        translation_chain = request.app.state.translation_chain
    except AttributeError:
        raise HTTPException(status_code=500, detail="Translation chain not initialized.")

    # For each FAQ, use the translation chain to translate the text.
    # The translation chain expects input variables "faq" and "target_lang".
    tasks = [
        asyncio.to_thread(translation_chain.invoke, {"faq": faq, "target_lang": target_lang})
        for faq in faq_questions
    ]
    results = await asyncio.gather(*tasks)
    
    # Assume the chain returns a dict with the key "text" containing the translation.
    translated_faqs = [result.get("text", "").strip() for result in results]
    logger.info("Translation complete")
    return JSONResponse(translated_faqs)
