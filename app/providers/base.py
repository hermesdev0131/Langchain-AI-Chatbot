# providers/base.py
from abc import ABC, abstractmethod
from typing import Any
from fastapi import UploadFile

class BaseProvider(ABC):
    @abstractmethod
    async def answer_query(self, query: str) -> dict:
        """Process the query using the provider's retrieval chain and return the result."""
        pass

    @abstractmethod
    async def get_faqs(self) -> dict:
        """Query FAQs and return results."""
        pass

    @abstractmethod
    async def translate_faqs(self, target_lang: str = 'en') -> list:
        """Translate FAQs and return results."""
        pass

    @abstractmethod
    async def transcribe_audio(self, file: UploadFile) -> str:
        """Transcribe the given audio file and return the transcript."""
        pass

    @abstractmethod
    async def search_data(self, query: str, limit: int, radius: float) -> dict:
        """Search for similar data and return."""
        pass

    @abstractmethod
    async def delete_document(self, id: str) -> dict:
        """Delete a single document with the given ID."""
        pass

    @abstractmethod
    async def delete_all_documents(self) -> dict:
        """Delete all documents."""
        pass