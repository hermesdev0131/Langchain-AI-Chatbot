from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/query")
async def handle_post(request: Request):
    """
    Receives a user query, uses the RAG chain to find relevant context 
    from Milvus, and returns the answer.
    """
    try:
        data = await request.json()
    except Exception as e:
        logger.error("Failed to parse request JSON: %s", e)
        raise HTTPException(status_code=400, detail="Invalid JSON request")
    
    user_message = data.get("userMessage", "No message provided")
    logger.info(f"Received user query: {user_message}")
    
    try:
        # Access the chain via request.app.state
        result = await asyncio.to_thread(request.app.state.retrieval_chain.invoke, {"query": user_message})
        logger.info(f"Retrieval Chain result: {result}")
    except Exception as e:
        logger.error("Error invoking retrieval chain: %s", e)
        raise HTTPException(status_code=500, detail="Retrieval Chain processing error")
    
    return JSONResponse({
        "response": result["result"],
    })
