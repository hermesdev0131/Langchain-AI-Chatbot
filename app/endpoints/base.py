from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
import aiofiles
import os

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def serve_index():
    file_path = os.path.join(os.path.dirname(__file__), "..", "..", "static", "index.html")
    try:
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
            content = await f.read()
        return HTMLResponse(content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="index.html not found")
