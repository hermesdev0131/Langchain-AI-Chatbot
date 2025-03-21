# faq.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/faqs")
async def get_faqs(request: Request):
    provider = request.app.state.provider
    faqs = await provider.query_faqs()
    logger.info("faq data: %s", faqs)

    return JSONResponse(faqs)

@router.get("/faqs/translate")
async def translate_faqs(request: Request, lang: str = 'en'):
    logger.info(f"Translating FAQs to {lang}")
    target_lang = lang.lower()
    
    provider = request.app.state.provider
    data = await provider.query_faqs()
    faq_questions = [record.get("faq") for record in data.get("data", []) if record.get("faq")]

    if target_lang == 'en':
        return JSONResponse(faq_questions)

    try:
        translation_chain = request.app.state.translation_chain
    except AttributeError:
        raise HTTPException(status_code=500, detail="Translation chain not initialized.")

    tasks = [
        asyncio.to_thread(translation_chain.invoke, {"faq": faq, "target_lang": target_lang})
        for faq in faq_questions
    ]
    results = await asyncio.gather(*tasks)
    
    translated_faqs = []
    for result in results:
        logger.info(f"Translation result: {result}")
        try:
            if hasattr(result, "dict"):
                text = result.dict().get("content", "")
            else:
                text = result
            translated_faqs.append(text.strip())
        except Exception as e:
            logger.error(f"Error processing translation result: {e}")
            translated_faqs.append("")
            
    logger.info(f"Translated {translated_faqs} FAQs to {target_lang}")
    return JSONResponse(translated_faqs)
