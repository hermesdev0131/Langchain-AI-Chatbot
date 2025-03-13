from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import requests
import pandas as pd
from app.config import settings
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/search_data")
async def search_data(query: str, limit: int = 100, radius: float = 0.8):
    """
    Generate a text embedding for the query, search for similar entries in the vectordb,
    and aggregate the results by hour.
    """
    collection_name = "user_queries"
    model_name = "text-embedding-3-large"

    # Generate embedding using OpenAI's client (offload blocking call)
    try:
        logger.info("Generating embedding for query: %s", query)
        embedding_response = await asyncio.to_thread(
            settings.client.embeddings.create, input=query, model=model_name
        )
        query_vector = embedding_response.data[0].embedding
        logger.debug("Embedding generated successfully: %s", query_vector)
    except Exception as e:
        logger.exception("Embedding generation failed")
        raise HTTPException(
            status_code=500, 
            detail=f"Embedding generation failed: {e}"
        )

    # Build the payload for the vectordb search
    payload = {
        "collectionName": collection_name,
        "data": [query_vector],
        "annsField": "vector",
        "limit": limit,
        "searchParams": {
            "metric_type": "COSINE",
            "params": {"nprobe": 10, "radius": radius}
        },
        "outputFields": ["pk", "timestamp"]
    }
    logger.debug("Payload for vectordb search: %s", payload)

    headers = {
        "Authorization": f"Bearer {settings.ZILLIZ_AUTH_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # Query the Zilliz vectordb and process the response
    try:
        search_url = f"{settings.ZILLIZ_URL}/v2/vectordb/entities/search"
        logger.info("Sending request to Zilliz URL: %s", search_url)
        response = requests.post(search_url, json=payload, headers=headers)
        response.raise_for_status()
        logger.debug("Response status code: %s", response.status_code)
        result = response.json()
        logger.debug("Response JSON: %s", result)

        # Convert response data to a DataFrame
        data = result.get("data", [])
        df = pd.DataFrame(data)
        if df.empty or "timestamp" not in df.columns:
            logger.warning("No data found or missing 'timestamp' field in response")
            return JSONResponse({"frequency": 0, "result": []})
        
        # Convert UNIX timestamp to datetime
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")
        # Group results by the hour and calculate frequency
        grouped = (
            df.groupby(df["datetime"].dt.floor("H"))
              .size()
              .reset_index(name="frequency")
        )
        grouped.sort_values(by="datetime", inplace=True)
        grouped["datetime"] = grouped["datetime"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        aggregated_results = grouped.to_dict(orient="records")
        total_frequency = int(grouped["frequency"].sum())

        logger.info("Successfully aggregated data with total frequency: %d", total_frequency)
    except Exception as e:
        logger.exception("Zilliz query failed")
        raise HTTPException(
            status_code=500, 
            detail=f"Zilliz query failed: {e}"
        )
    
    return JSONResponse({"frequency": total_frequency, "result": aggregated_results})
