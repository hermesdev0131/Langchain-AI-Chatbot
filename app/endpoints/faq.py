from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/faqs")
async def get_faqs(request: Request):
    provider = request.state.provider
    try:
        faq_texts = await provider.get_faqs()
        logger.info("FAQs: %s", faq_texts)
        return JSONResponse(faq_texts)
    except Exception as e:
        logger.error(f"Failed to retrieve FAQs: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/faqs/translate")
async def translate_faqs(request: Request, lang: str = 'en'):
    provider = request.state.provider
    try:
        translated_faqs = await provider.translate_faqs(target_lang=lang)
        logger.info("Translated FAQs: %s", translated_faqs)
        return JSONResponse(translated_faqs)
    except Exception as e:
        logger.error(f"Failed to translate FAQs: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)
