from fastapi import Request
from app.config import settings

def set_azure_provider(request: Request):
    request.state.provider = request.app.state.azure_provider
    request.state.template = {**settings.WICHITA_TEMPLATE, "api_base_url": "/wichita/api"}

def set_zilliz_provider(request: Request):
    request.state.provider = request.app.state.zilliz_provider
    request.state.template = {**settings.WSU_TEMPLATE, "api_base_url": "/wsu/api"}