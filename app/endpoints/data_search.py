# data_search.py

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/data_search")
async def search_data(request: Request, query: str, limit: int = 100, radius: float = 0.8):
    """
    Delegates to the provider's search_data method.
    """
    try:
        result = await request.state.provider.search_data(query, limit, radius)
        return JSONResponse(result)
    except Exception as e:
        logger.exception("Search data error")
        raise HTTPException(status_code=500, detail=str(e))
