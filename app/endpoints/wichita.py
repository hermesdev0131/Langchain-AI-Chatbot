from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from datetime import datetime
from app.dependencies import set_azure_provider

router = APIRouter(dependencies=[Depends(set_azure_provider)])
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "..", "static", "templates"))

@router.get("/wichita", response_class=HTMLResponse)
async def serve_index(request: Request):
    context = {
        **request.state.template,
        "request": request,
        "show_dashboard": False,
        "current_year": datetime.now().year
    }
    return templates.TemplateResponse("index.html", context)
