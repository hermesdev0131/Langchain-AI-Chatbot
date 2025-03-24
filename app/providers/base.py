# providers/base.py
from abc import ABC, abstractmethod
from typing import Any
from fastapi import UploadFile

class BaseProvider(ABC):
    @abstractmethod
    async def initialize_vector_store(self) -> Any:
        """Initialize the vector store and return any necessary state."""
        pass

    @abstractmethod
    async def initialize_retrieval_chain(self, vector_store: Any, cached_embeddings: Any) -> Any:
        """Initialize and return the retrieval chain."""
        pass

    @abstractmethod
    async def initialize_ingest_chain(self):
        """Initialize and return ingest chain."""
        pass

    @abstractmethod
    async def initialize_translation_chain(self):
        """Initialize and return translation chain."""
        pass

    @abstractmethod
    async def query_faqs(self) -> dict:
        """Query FAQs and return results."""
        pass

    @abstractmethod
    async def transcribe_audio(self, file: "UploadFile") -> str:
        """Transcribe the given audio file and return the transcript."""
        pass