from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
from app.chains.retrieval_chain_azure import answer_query

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/qa")
async def handle_post(request: Request):
    """
    Receives a user query, uses the RAG chain to find relevant context (innovation_campus),
    then inserts the user query doc into user_queries. Returns the final answer.
    """
    try:
        data = await request.json()
    except Exception as e:
        logger.error("Failed to parse request JSON: %s", e)
        raise HTTPException(status_code=400, detail="Invalid JSON request")
    
    user_message = data.get("userMessage", "No message provided")
    logger.info(f"Received user query: {user_message}")
    
    try:
        # The chain wrapper is stored in app.state
        wrapper = request.app.state.retrieval_chain_wrapper
        result = await answer_query(user_message, wrapper)
        logger.info(f"Answer: {result}")
    except Exception as e:
        logger.error("Error processing retrieval chain: %s", e)
        raise HTTPException(status_code=500, detail="Processing error")
    
    return JSONResponse({"response": result["result"]})
