from fastapi import APIRouter, Request, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/ingest_document")
async def ingest_document(request: Request, file: UploadFile = File(...)):
    """
    Receives an uploaded document, processes it using the ingestion chain,
    and ingests its contents into vector_store
    """
    try:
        contents = await file.read()
    except Exception as e:
        logger.error("Failed to read uploaded file: %s", e)
        raise HTTPException(status_code=400, detail="Failed to read file")
    
    try:
        result = await request.state.provider.ingest_chain.ingest_document(contents, file.filename)
    except Exception as e:
        logger.error("Ingestion chain error: %s", e)
        raise HTTPException(status_code=500, detail="Ingestion failed")
        
    return JSONResponse(result)

@router.post("/ingest_url")
async def ingest_document(request: Request):
    """
    Receives a url, processes it using the ingestion chain,
    and ingests its contents into vector_store
    """
    try:
        data = await request.json()
    except Exception as e:
        logger.error("Failed to read uploaded file: %s", e)
        raise HTTPException(status_code=400, detail="Failed to read file")
    
    url = data.get("url")
    
    try:
        result = await request.state.provider.ingest_chain.ingest_url(url)
    except Exception as e:
        logger.error("Ingestion chain error: %s", e)
        raise HTTPException(status_code=500, detail="Ingestion failed")
        
    return JSONResponse(result)