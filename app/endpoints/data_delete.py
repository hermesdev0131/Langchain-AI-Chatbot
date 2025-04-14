from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/document_delete")
async def document_delete(request: Request, id: str = Query(..., description="The ID of the document to delete")):
    """
    Deletes a single document from the provider.
    Called with a query parameter, e.g.:
      localhost:8000/api/document_delete?id=DOCUMENT_ID
    """
    logger.debug(f"Received request to delete document with id: {id}")
    try:
        result = await request.state.provider.delete_document(id)
        logger.info(f"Document {id} deleted successfully with result: {result}")
    except Exception as e:
        logger.error("Document deletion error for id %s: %s", id, e)
        raise HTTPException(status_code=500, detail="Document deletion failed")
        
    return JSONResponse(content=result)

@router.get("/document_delete_all")
async def document_delete_all(request: Request):
    """
    Deletes all documents from the provider.
    Called without parameters, e.g.:
      localhost:8000/api/document_delete_all
    """
    logger.debug("Received request to delete all documents")
    try:
        result = await request.state.provider.delete_all_documents()
        logger.info(f"All documents deleted successfully with result: {result}")
    except Exception as e:
        logger.error("Delete all documents error: %s", e)
        raise HTTPException(status_code=500, detail="Delete all documents failed")
        
    return JSONResponse(content=result)
