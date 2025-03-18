from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

router = APIRouter()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "..", "static", "templates"))

@router.get("/chatbot", response_class=HTMLResponse)
async def serve_index(request: Request):
    # Pass dynamic UI configurations here
    WSU_template = {
        "request": request,
        "title": "WSU Chatbot Dashboard",
        "hero_img": "/static/img/chatbot_hero_back_WSU.png",
        "hero_overlay_img": "https://cdn.freelogovectors.net/wp-content/uploads/2023/10/wichita-state-university-logo-freelogovectors.net_.png",
        "chatbot_button_img": "https://upload.wikimedia.org/wikipedia/en/thumb/9/90/Wichita_State_Shockers_logo.svg/300px-Wichita_State_Shockers_logo.svg.png",
        "chatbot_background_img": "https://cdn.freebiesupply.com/logos/large/2x/wichita-state-shockers-1-logo-black-and-white.png",
        "hero_alt": "Wichita State University Logo",
        "chatbot_name": "Shocker Assistant",
        "unified_color": "#FFC000",
        "text_color": "#FFFFFF",
    }
    Wichita_template = {
        "request": request,
        "title": "Wichita Chatbot Dashboard",
        "hero_img": "/static/img/chatbot_hero_back_wichita.png",
        "hero_overlay_img": "/static/img/chatbot_hero_front_wichita.png",
        "chatbot_button_img": "/static/img/chatbot_button_wichita.png",
        "chatbot_background_img": "/static/img/chatbot_button_wichita.png",
        "hero_alt": "City of Wichita",
        "chatbot_name": "Wichita Assistant",
        "unified_color": "#0047AB",
        "text_color": "#FFFFFF",
    }
    template = Wichita_template
    return templates.TemplateResponse("chatbot.html", template)
