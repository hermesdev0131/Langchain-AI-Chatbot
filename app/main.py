import os
import uvicorn
import logging
import time # Added import
from fastapi import FastAPI, Request, Response, APIRouter, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse # Added JSONResponse
from contextlib import asynccontextmanager
from app import *
from app.config import settings
from app.dependencies import set_azure_provider, set_zilliz_provider

logger = logging.getLogger(__name__)

# Rate limiting configuration
API_RATE_LIMIT = 60  # Max API requests per IP per minute
API_RATE_WINDOW = 60  # Seconds
api_user_requests = {} # Stores IP and their request timestamps for API routes

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

# Rate limiting middleware for API routes
@app.middleware("http")
async def rate_limit_api_requests(request: Request, call_next):
    # Check if the path is an API path we want to rate limit
    if "/api/" in request.url.path:
        
        user_ip = request.client.host if request.client else "unknown_client" # Get client IP
        current_time = time.time()

        # Get existing timestamps for this IP, or an empty list if new IP
        request_timestamps = api_user_requests.get(user_ip, [])
        
        # Filter out timestamps older than the rate limit window
        valid_timestamps = [t for t in request_timestamps if current_time - t < API_RATE_WINDOW]
        
        if len(valid_timestamps) >= API_RATE_LIMIT:
            logger.warning(f"API rate limit exceeded for IP {user_ip} on path {request.url.path}")
            return JSONResponse(
                status_code=429, # HTTP 429 Too Many Requests
                content={"detail": "Rate limit exceeded. Please try again later."}
            )
        
        # Add current request timestamp and update the store
        valid_timestamps.append(current_time)
        api_user_requests[user_ip] = valid_timestamps

    # Proceed with the request if not rate-limited
    response = await call_next(request)
    return response

# allows framing
@app.middleware("http")
async def frame_control(request: Request, call_next):
    response: Response = await call_next(request)
    # Only allow framing if the request is for the /api/chatbot endpoint
    if request.url.path.startswith("/wsu/api/chatbot"):
        response.headers["Content-Security-Policy"] = "frame-ancestors http://localhost:3000 https://www.wichita.edu;"
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
# Provider-specific API routers
# -------------------------------------------------
# Wichita API: endpoints will be available at /wichita/api/...
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
