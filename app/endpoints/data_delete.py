from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from app.chains.delete_documents_azure import delete_document, delete_all_documents
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/document_delete")
async def document_delete(document_id: str = Query(..., description="The ID of the document to delete")):
    """
    Deletes a document from the Azure AI Search index.
    Called with a query parameter, e.g.:
      localhost:8000/api/document_delete?document_id=DOCUMENT_ID
    """
    try:
        result = await delete_all_documents()
    except Exception as e:
        logger.error("Document deletion error: %s", e)
        raise HTTPException(status_code=500, detail="Document deletion failed")
        
    return JSONResponse(content=result)
