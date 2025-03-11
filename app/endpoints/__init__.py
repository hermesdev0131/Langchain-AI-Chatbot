# app/endpoints/__init__.py

from .base import router as base_router
from .search import router as search_router
from .faq import router as faq_router
from .transcribe import router as transcribe_router
from .query import router as query_router

__all__ = ["base_router", "query_router", "search_router", "faq_router", "transcribe_router"]
