from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    RENDER_LANGFLOW_API_KEY: Optional[str] = "http://default.api.url"
    ZILLIZ_AUTH_TOKEN: Optional[str] = "http://default.api.url"
    ZILLIZ_URL: Optional[str] = "http://default.api.url"
    OPENAI_API_KEY: Optional[str] = "http://default.api.url"
    LANGFLOW_BASE_API_URL: Optional[str] = "http://default.api.url"
    FLOW_ID: Optional[str] = "http://default.api.url"
    PORT: int = 8000  # Default port for local development

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }
