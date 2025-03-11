from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import requests
import pandas as pd
from app.config import settings
from app import config

router = APIRouter()

@router.get("/search_data")
async def search_data(query: str, limit: int = 100, radius: float = 0.8):
    collection_name = "user_queries"
    model_name = "text-embedding-3-large"

    try:
        # Generate embedding using OpenAI's client (blocking call offloaded)
        embedding_response = await asyncio.to_thread(
            config.client.embeddings.create, input=query, model=model_name
        )
        query_vector = embedding_response.data[0].embedding
    except Exception as e:
        raise HTTPException(status_code=500, detail="Embedding generation failed: " + str(e))

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
    
    headers = {
        "Authorization": f"Bearer {settings.ZILLIZ_AUTH_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(settings.ZILLIZ_URL + "/v2/vectordb/entities/search", json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        data = result.get("data", [])
        df = pd.DataFrame(data)
        if df.empty or "timestamp" not in df.columns:
            return JSONResponse({"frequency": 0, "result": []})
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")
        grouped = df.groupby(df["datetime"].dt.floor("H")).size().reset_index(name="frequency")
        grouped.sort_values(by="datetime", inplace=True)
        grouped["datetime"] = grouped["datetime"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        aggregated_results = grouped.to_dict(orient="records")
        total_frequency = int(grouped["frequency"].sum())
    except Exception as e:
        raise HTTPException(status_code=500, detail="Zilliz query failed: " + str(e))
    
    return JSONResponse({"frequency": total_frequency, "result": aggregated_results})
