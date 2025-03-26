import os
import uvicorn
import logging
from fastapi import FastAPI, Request, Response, APIRouter, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from app import *

logger = logging.getLogger(__name__)

# runs at startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Startup: initializing chains...")
    
    # Initialize Azure Provider
    azure_provider = await AzureProvider.create()
    app.state.azure_provider = azure_provider

    # Initialize Zilliz Provider
    zilliz_provider = await ZillizProvider.create()
    app.state.zilliz_provider = zilliz_provider

    logger.info("Chains stored in app state.")
    yield
    logger.info("Shutdown: cleaning up resources...")

app = FastAPI(lifespan=lifespan)

# origin control
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# allows framing
@app.middleware("http")
async def frame_control(request: Request, call_next):
    response: Response = await call_next(request)
    # Only allow framing if the request is for the /api/chatbot endpoint
    if request.url.path.startswith("/api/chatbot"):
        response.headers["Content-Security-Policy"] = "frame-ancestors http://localhost:3000"
    else:
        response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
    return response


# Mount static files
static_folder = os.path.join(os.path.dirname(__file__), "..", "static")
app.mount("/static", StaticFiles(directory=static_folder), name="static")

# Redirect to /wichita route by default
@app.get("/")
async def default_route():
    return RedirectResponse(url="/wichita")

# -------------------------------------------------
# Provider-specific dependency functions
# -------------------------------------------------
def set_azure_provider(request: Request):
    request.state.provider = request.app.state.azure_provider

def set_zilliz_provider(request: Request):
    request.state.provider = request.app.state.zilliz_provider

# -------------------------------------------------
# Provider-specific API routers
# -------------------------------------------------
# Wichita API: endpoints will be available at /api/...
wichita_api_router = APIRouter(prefix="/wichita", dependencies=[Depends(set_azure_provider)])
wichita_api_router.include_router(chatbot_router, prefix="/api")
wichita_api_router.include_router(ingest_router, prefix="/api")
wichita_api_router.include_router(data_delete_router, prefix="/api")
wichita_api_router.include_router(qa_router, prefix="/api")
wichita_api_router.include_router(data_search_router, prefix="/api")
wichita_api_router.include_router(faq_router, prefix="/api")
wichita_api_router.include_router(transcribe_router, prefix="/api")

# WSU API: endpoints will be available at /wsu/api/...
wsu_api_router = APIRouter(prefix="/wsu", dependencies=[Depends(set_zilliz_provider)])
wsu_api_router.include_router(chatbot_router, prefix="/api")
wsu_api_router.include_router(ingest_router, prefix="/api")
wsu_api_router.include_router(data_delete_router, prefix="/api")
wsu_api_router.include_router(qa_router, prefix="/api")
wsu_api_router.include_router(data_search_router, prefix="/api")
wsu_api_router.include_router(faq_router, prefix="/api")
wsu_api_router.include_router(transcribe_router, prefix="/api")

# -------------------------------------------------
# Include non-API routes and provider-specific API routers
# -------------------------------------------------
app.include_router(wichita_router)
app.include_router(wsu_router)
app.include_router(wichita_api_router)
app.include_router(wsu_api_router)

if __name__ == '__main__':
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=False)
