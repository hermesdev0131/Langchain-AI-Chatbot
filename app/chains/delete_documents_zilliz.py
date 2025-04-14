import httpx
from app.config import settings
import logging

logger = logging.getLogger(__name__)

async def delete_document(document_id: str) -> dict:
    """
    Delete a single document in Zilliz Cloud.
    """
    logger.debug(f"Deleting document with {settings.ZILLIZ_PRIMARY_KEY_FIELD_NAME}: {document_id}")
    
    url = f"{settings.ZILLIZ_URL}/v2/vectordb/entities/delete"
    
    payload = {
        "collectionName": settings.ZILLIZ_COLLECTION_NAME,
        "filter": f"{settings.ZILLIZ_PRIMARY_KEY_FIELD_NAME} in [{document_id}]"
    }
    headers = {
        "Authorization": f"Bearer {settings.ZILLIZ_AUTH_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    logger.debug(f"Sending DELETE request to {url} with payload: {payload}")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        logger.debug(f"Received response status {response.status_code} for delete_document")
        response.raise_for_status()
        result = response.json()
    
    logger.info(f"Document deletion response for {settings.ZILLIZ_PRIMARY_KEY_FIELD_NAME} {document_id}: {result}")
    return {"deleted": result}


async def delete_all_documents() -> dict:
    """
    Delete all documents in the Zilliz Cloud collection by first querying for their primary keys (pk)
    and then deleting them in batches using a filter expression.
    """
    logger.debug("Querying all document IDs (primary keys) for deletion")
    
    query_url = f"{settings.ZILLIZ_URL}/v2/vectordb/entities/query"
    delete_url = f"{settings.ZILLIZ_URL}/v2/vectordb/entities/delete"
    query_payload = {
        "collectionName": settings.ZILLIZ_COLLECTION_NAME,
        "outputFields": [settings.ZILLIZ_PRIMARY_KEY_FIELD_NAME],
        "limit": 1000
    }
    headers = {
        "Authorization": f"Bearer {settings.ZILLIZ_AUTH_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    document_ids = []
    async with httpx.AsyncClient() as client:
        # Query the collection for document primary keys.
        response = await client.post(query_url, json=query_payload, headers=headers)
        logger.debug("Query response status: %s", response.status_code)
        response.raise_for_status()
        result = response.json()
        logger.debug("Query response content: %s", result)
        
        # Extract primary keys from the query result.
        for item in result.get("data", []):
            if settings.ZILLIZ_PRIMARY_KEY_FIELD_NAME in item:
                document_ids.append(item[settings.ZILLIZ_PRIMARY_KEY_FIELD_NAME])
                
        if not document_ids:
            logger.info("No documents found for deletion.")
            return {"message": "No documents found."}
        
        logger.info("Found %d documents for deletion.", len(document_ids))
        
        # Delete documents in batches using filter expressions.
        batch_size = 100
        deletion_results = []
        for i in range(0, len(document_ids), batch_size):
            batch_ids = document_ids[i : i + batch_size]

            deletion_payload = {
                "collectionName": settings.ZILLIZ_COLLECTION_NAME,
                "filter": f"{settings.ZILLIZ_PRIMARY_KEY_FIELD_NAME} in [{', '.join(str(id) for id in batch_ids)}]"
            }

            del_response = await client.post(delete_url, json=deletion_payload, headers=headers)
            logger.debug("Batch deletion response status: %s", del_response.status_code)
            del_response.raise_for_status()

            deletion_result = del_response.json()
            logger.info("Batch %d deletion result: %s", i // batch_size + 1, deletion_result)
            deletion_results.append(deletion_result)
    
    logger.info("Total documents deleted: %d", len(document_ids))
    return {"deleted_batches": deletion_results, "total_deleted": len(document_ids)}