from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from app.config import settings

router = APIRouter()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "..", "static", "templates"))

@router.get("/wichita", response_class=HTMLResponse)
async def serve_index(request: Request):
    template = {**settings.WICHITA_TEMPLATE, "request": request, "api_base_url": "/wichita/api", "show_dashboard": False}

    return templates.TemplateResponse("index.html", template)
