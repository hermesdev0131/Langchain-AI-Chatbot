from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential
from app.config import settings
from fastapi.responses import JSONResponse

async def delete_document(document_id: str):
    search_client = SearchClient(
        endpoint=settings.AZURE_AI_SEARCH_ENDPOINT,
        index_name=settings.AZURE_INDEX_NAME,
        credential=AzureKeyCredential(settings.AZURE_AI_SEARCH_API_KEY)
    )
    async with search_client:
        batch = [{"@search.action": "delete", "id": document_id}]
        result = await search_client.upload_documents(documents=batch)
        # Convert IndexingResult objects to dictionaries
        serialized_result = [
            {
                "key": r.key,
                "status": r.status,
                "errorMessage": r.error_message,
                "statusCode": r.status_code
            }
            for r in result
        ]
        # Return JSONResponse or just return serialized_result in your endpoint
        return JSONResponse(content=serialized_result)
    
    
async def delete_all_documents():
    search_client = SearchClient(
        endpoint=settings.AZURE_AI_SEARCH_ENDPOINT,
        index_name=settings.AZURE_INDEX_NAME,
        credential=AzureKeyCredential(settings.AZURE_AI_SEARCH_API_KEY)
    )
    document_ids = []
    
    # Retrieve all documents (assuming your key field is "id")
    async with search_client:
        # Use "*" to retrieve all documents. You may need to set a high `top` value or use pagination.
        results = search_client.search("*", select=["id"], top=1000)
        async for doc in results:
            # Assuming the document key field is "id"
            document_ids.append(doc["id"])
    
    # If no documents found, return early.
    if not document_ids:
        return JSONResponse(content={"message": "No documents found."})
    
    # Delete in batches (Azure has limits on batch sizes; 100 is a safe batch size)
    batch_size = 100
    deletion_results = []
    for i in range(0, len(document_ids), batch_size):
        batch_ids = document_ids[i : i + batch_size]
        deletion_batch = [{"@search.action": "delete", "id": doc_id} for doc_id in batch_ids]
        async with search_client:
            result = await search_client.upload_documents(documents=deletion_batch)
        # Serialize results for logging/response
        serialized = [
            {
                "key": r.key,
                "status": r.status,
                "errorMessage": r.error_message,
                "statusCode": r.status_code
            }
            for r in result
        ]
        deletion_results.append(serialized)
    
    return JSONResponse(content={"deleted_batches": deletion_results, "total_deleted": len(document_ids)})