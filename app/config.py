from openai import OpenAI
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SYSTEM_PROMPT: str = (
        "Please answer the question below in up to 5 sentences (not including any extra links), or give information, following these rules:\n"
        "1. Only use information explicitly contained in the context.\n"
        "2. If the context contains relevant links (for images, videos, or external pages) that relate to any topic, include them exactly as provided.\n"
        "3. Include image, video, and external links related to the question, even if not explicitly requested. Prioritize image and video links.\n"
        "4. Do not fabricate or guess any links that are not in the context.\n"
        "6. If there isn’t enough detail, respond with: \"I do not have enough information from the provided context.\"\n"
        "7. When including links in your responses, please output the full URL in plain text rather than using HTML or Markdown anchor formatting.\n"
        "8. When including images, put them on a new line"
    )
    OPENAI_API_CHAT_MODEL_NAME: str = "gpt-4o-mini"
    OPENAI_API_EMBEDDING_MODEL_NAME: str = "text-embedding-3-large"
    OPENAI_API_KEY: str
    ZILLIZ_AUTH_TOKEN: str
    ZILLIZ_URL: str
    ZILLIZ_COLLECTION_NAME: str = "innovation_campus"
    ZILLIZ_USER_QUERIES_COLLECTION_NAME: str = "user_queries"
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_KEY: str
    AZURE_AI_SEARCH_ENDPOINT: str
    AZURE_AI_SEARCH_API_KEY: str
    AZURE_MODEL_NAME:str = "gpt-4o-mini"
    AZURE_DEPLOYMENT_NAME: str = "gpt-4o-mini"
    AZURE_API_VERSION: str = "2024-07-01-preview"
    AZURE_INDEX_NAME: str = "chatbot-index"
    REQUEST_TIMEOUT: int = 50_000
    TEMPERATURE: int = 0
    CHUNK_SIZE: int = 4000
    CHUNK_OVERLAP: int = 400
    PORT: int = 8000

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def client(self) -> OpenAI:
        return OpenAI(api_key=self.OPENAI_API_KEY)

settings = Settings()
