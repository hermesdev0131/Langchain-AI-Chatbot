from fastapi import APIRouter, Request, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from app.chains.ingest_chain_azure import initialize_ingest_chain
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/ingest")
async def ingest_document(request: Request, file: UploadFile = File(...)):
    """
    Receives an uploaded document, processes it using the ingestion chain,
    and ingests its contents into Azure AI Search.
    """
    try:
        contents = await file.read()
    except Exception as e:
        logger.error("Failed to read uploaded file: %s", e)
        raise HTTPException(status_code=400, detail="Failed to read file")
    
    try:
        result = await request.state.provider.ingest_chain(contents, file.filename)
    except Exception as e:
        logger.error("Ingestion chain error: %s", e)
        raise HTTPException(status_code=500, detail="Ingestion failed")
        
    return JSONResponse(result)
