from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential
from app.config import settings
from fastapi.responses import JSONResponse

async def delete_document(document_id: str) -> dict:
    search_client = SearchClient(
        endpoint=settings.AZURE_AI_SEARCH_ENDPOINT,
        index_name=settings.AZURE_INDEX_NAME,
        credential=AzureKeyCredential(settings.AZURE_AI_SEARCH_API_KEY)
    )
    async with search_client:
        batch = [{"@search.action": "delete", "id": document_id}]
        result = await search_client.upload_documents(documents=batch)
        serialized_result = [
            {
                "key": r.key,
                "succeeded": r.succeeded,
                "errorMessage": r.error_message,
                "statusCode": r.status_code
            }
            for r in result
        ]
        return {"deleted": serialized_result}
    
    
async def delete_all_documents() -> dict:
    search_client = SearchClient(
        endpoint=settings.AZURE_AI_SEARCH_ENDPOINT,
        index_name=settings.AZURE_INDEX_NAME,
        credential=AzureKeyCredential(settings.AZURE_AI_SEARCH_API_KEY)
    )
    document_ids = []
    
    async with search_client:
        results = await search_client.search("*", select=["id"], top=1000)
        async for doc in results:
            document_ids.append(doc["id"])
    
        if not document_ids:
            return {"message": "No documents found."}
    
        batch_size = 100
        deletion_results = []
        for i in range(0, len(document_ids), batch_size):
            batch_ids = document_ids[i : i + batch_size]
            deletion_batch = [{"@search.action": "delete", "id": doc_id} for doc_id in batch_ids]
            result = await search_client.upload_documents(documents=deletion_batch)
            serialized = [
                {
                    "key": r.key,
                    "succeeded": r.succeeded,
                    "errorMessage": r.error_message,
                    "statusCode": r.status_code
                }
                for r in result
            ]
            deletion_results.append(serialized)
    
    return {"deleted_batches": deletion_results, "total_deleted": len(document_ids)}
