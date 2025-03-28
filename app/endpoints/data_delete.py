from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from app.chains.delete_documents_azure import delete_document, delete_all_documents
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/document_delete")
async def document_delete(id: str = Query(..., description="The ID of the document to delete")):
    """
    Deletes a document from the Azure AI Search index.
    Called with a query parameter, e.g.:
      localhost:8000/api/document_delete?id=DOCUMENT_ID
    """
    try:
        #TODO move to provider
        #TODO add delete document for zilliz
        result = await delete_document(id)
    except Exception as e:
        logger.error("Document deletion error: %s", e)
        raise HTTPException(status_code=500, detail="Document deletion failed")
        
    return JSONResponse(content=result)
