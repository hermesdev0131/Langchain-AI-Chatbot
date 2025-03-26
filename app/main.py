import os
import uvicorn
import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app import *

logger = logging.getLogger(__name__)

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def frame_control(request: Request, call_next):
    response: Response = await call_next(request)
    # If the request is for the base domain, disallow framing.
    if request.url.path == "/":
        response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
    else:
        response.headers["Content-Security-Policy"] = "frame-ancestors http://localhost:3000"
    return response

# Mount static files
static_folder = os.path.join(os.path.dirname(__file__), "..", "static")
app.mount("/static", StaticFiles(directory=static_folder), name="static")

# Include endpoints
app.include_router(wichita_router)
app.include_router(wsu_router)
app.include_router(chatbot_router)
app.include_router(ingest_router, prefix="/api")
app.include_router(data_delete_router, prefix="/api")
app.include_router(qa_router, prefix="/api")
app.include_router(data_search_router, prefix="/api")
app.include_router(faq_router, prefix="/api")
app.include_router(transcribe_router, prefix="/api")

if __name__ == '__main__':
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=False)
