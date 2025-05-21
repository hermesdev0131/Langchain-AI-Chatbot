# providers/base.py
from abc import ABC, abstractmethod
from fastapi import UploadFile
import logging

logger = logging.getLogger(__name__)

class BaseProvider(ABC):
    @abstractmethod
    async def answer_query(self, query: str) -> dict:
        """
        Process a user query and return a complete answer.
        This is typically used for non-streaming responses.
        """
        pass

    async def answer_query_stream(self, query: str):
        """
        Default implementation for streaming query responses.
        Calls the provider's non-streaming `answer_query` method and yields the full result.
        Providers should override this if they support true token-by-token streaming.
        """
        logger.debug( # Changed from logger.info to logger.debug
            f"Provider {self.__class__.__name__} does not have a specific streaming implementation for 'answer_query_stream'. "
            f"Falling back to use non-streaming 'answer_query' for query: '{query[:100]}...'"
        )
        try:
            # Call the mandatory answer_query method
            result_dict = await self.answer_query(query)
            full_answer = result_dict.get("result")

            if full_answer is not None:
                yield full_answer
            else:
                logger.error(
                    f"answer_query for {self.__class__.__name__} did not return a 'result' field for query: '{query[:100]}...'"
                )
                yield "Error: Could not retrieve answer."
        except Exception as e:
            logger.error(
                f"Error in fallback answer_query_stream for {self.__class__.__name__} using answer_query: {e}",
                exc_info=True
            )
            yield "Error: An unexpected error occurred while processing your request."
        return # Ensure the async generator properly completes

    @abstractmethod
    async def get_faqs(self) -> dict:
        """
        Retrieve Frequently Asked Questions.
        The structure of the returned dict may vary by provider.
        """
        pass

    @abstractmethod
    async def translate_faqs(self, target_lang: str = 'en') -> list:
        """
        Translate FAQs to the specified target language.
        Should return a list of translated FAQ items.
        """
        pass

    @abstractmethod
    async def transcribe_audio(self, file: UploadFile) -> str:
        """
        Transcribe an uploaded audio file to text.
        Returns the transcription as a string.
        """
        pass

    @abstractmethod
    async def search_data(self, query: str, limit: int, radius: float) -> dict:
        """
        Search for data related to the query, typically for analytics or similar queries.
        """
        pass

    @abstractmethod
    async def delete_document(self, id: str) -> dict:
        """
        Delete a single document identified by its ID from the underlying data store.
        Returns a status message.
        """
        pass

    @abstractmethod
    async def delete_all_documents(self) -> dict:
        """
        Delete all documents from the relevant collection(s) in the underlying data store.
        Returns a status message.
        """
        pass