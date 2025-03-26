# faq.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def extract_faq_texts(data: dict) -> list:
    """
    Extracts FAQ texts from the provider's response.
    Handles cases where the 'faq' field may be a string, a dict, or a list.
    """
    faq_texts = []
    for record in data.get("data", []):
        faq_val = record.get("faq")
        if faq_val:
            if isinstance(faq_val, list):
                for item in faq_val:
                    if isinstance(item, dict):
                        faq_texts.append(item.get("heading", "").strip())
                    else:
                        faq_texts.append(str(item).strip())
            elif isinstance(faq_val, dict):
                faq_texts.append(faq_val.get("heading", "").strip())
            else:
                faq_texts.append(str(faq_val).strip())
    return faq_texts

def extract_translated_text(result) -> str:
    try:
        if isinstance(result, dict):
            # Try "heading", then fallback to "content"
            text = result.get("heading", "") or result.get("content", "")
        elif hasattr(result, "dict"):
            data = result.dict()
            text = data.get("heading", "") or data.get("content", "")
        else:
            text = result
        return text.strip() if isinstance(text, str) else str(text).strip()
    except Exception as e:
        logger.error(f"Error processing translation result: {e}")
        return ""


@router.get("/faqs")
async def get_faqs(request: Request):
    provider = request.state.provider
    data = await provider.query_faqs()
    logger.info("FAQ data: %s", data)
    # Use the unified helper to extract FAQs as a list of strings.
    faq_texts = extract_faq_texts(data)
    return JSONResponse(faq_texts)

# TODO put faqs into state, memory or something
# TODO see about launching tasks via provider class instead of on route
@router.get("/faqs/translate")
async def translate_faqs(request: Request, lang: str = 'en'):
    logger.info(f"Translating FAQs to {lang}")
    target_lang = lang.lower()
    
    provider = request.state.provider
    data = await provider.query_faqs()
    # Get a unified list of FAQ texts.
    faq_texts = extract_faq_texts(data)

    # If English is selected, return the FAQs as is.
    if target_lang == 'en':
        return JSONResponse(faq_texts)

    # Launch translation tasks concurrently.
    tasks = [
        asyncio.to_thread(provider.translation_chain.invoke, {"faq": faq, "target_lang": target_lang})
        for faq in faq_texts
    ]
    results = await asyncio.gather(*tasks)

    # Extract translated text using the helper.
    translated_faqs = [extract_translated_text(result) for result in results]
    logger.info(f"Translated {translated_faqs} FAQs to {target_lang}")
    return JSONResponse(translated_faqs)
