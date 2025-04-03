from pydantic_settings import BaseSettings
from typing import ClassVar

class Settings(BaseSettings):
    OPENAI_API_CHAT_MODEL_NAME: str = "gpt-4o-mini"
    OPENAI_API_EMBEDDING_MODEL_NAME: str = "text-embedding-3-large"
    OPENAI_API_KEY: str
    ZILLIZ_AUTH_TOKEN: str
    ZILLIZ_URL: str
    ZILLIZ_COLLECTION_NAME: str = "innovation_campus"
    ZILLIZ_USER_QUERIES_COLLECTION_NAME: str = "user_queries"
    ZILLIZ_VECTOR_FIELD_NAME: str = "vector"
    ZILLIZ_VECTOR_TEXT_FIELD_NAME: str = "vector_content"

    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_KEY: str
    AZURE_AI_SEARCH_ENDPOINT: str
    AZURE_AI_SEARCH_API_KEY: str
    AZURE_SPEECH_ENDPOINT: str
    AZURE_SPEECH_API_KEY: str
    AZURE_MONGO_CONNECTION_STRING: str
    AZURE_MONGO_DATABASE_NAME: str = "chatbot-cosmos-mongo-db"
    AZURE_MODEL_NAME: str = "gpt-4o-mini"
    AZURE_DEPLOYMENT_NAME: str = "gpt-4o-mini"
    AZURE_API_VERSION: str = "2024-07-01-preview"
    AZURE_INDEX_NAME: str = "chatbot-index"

    REQUEST_TIMEOUT: int = 50_000
    TEMPERATURE: int = 0
    CHUNK_SIZE: int = 4000
    CHUNK_OVERLAP: int = 400
    PORT: int = 8000
    MAX_GENERATED_SENTENCES: int = 5
    SYSTEM_PROMPT: str = (
        "1. Only use information explicitly contained in the context.\n"
        "2. Do not fabricate or guess any links that are not in the context.\n"
        "3. Keep all [embed] tags exactly as provided in the input, and do not alter or replace the [embed] text with any other labels.\n"
        "4. When including links in your responses, output the full URL in plain text but do not alter links with [embed] tag.\n"
        "5. When including images, always put them on a new line.\n"
        "6. When including videos, do not output any empty parentheses; instead, display the iframe on its own line without extra punctuation."
    )

    WSU_TEMPLATE: ClassVar[dict] = {
        "title": "WSU Chatbot Dashboard",
        "hero_img": "/static/img/chatbot_hero_back_WSU.png",
        "hero_overlay_img": "https://cdn.freelogovectors.net/wp-content/uploads/2023/10/wichita-state-university-logo-freelogovectors.net_.png",
        "chatbot_button_img": "https://upload.wikimedia.org/wikipedia/en/thumb/9/90/Wichita_State_Shockers_logo.svg/300px-Wichita_State_Shockers_logo.svg.png",
        "chatbot_background_img": "https://cdn.freebiesupply.com/logos/large/2x/wichita-state-shockers-1-logo-black-and-white.png",
        "hero_alt": "Wichita State University Logo",
        "chatbot_name": "Shocker Assistant",
        "unified_color": "#FFC000",
        "unified_color_light": "#ffd963",
        "unified_color_dark": "#bf9104",
        "unified_color_secondary": "#000000",
        "text_color": "#000000",
    }
    WICHITA_TEMPLATE: ClassVar[dict] = {
        "title": "Wichita Chatbot Dashboard",
        "hero_img": "/static/img/chatbot_hero_back_wichita.png",
        "hero_overlay_img": "/static/img/chatbot_hero_front_wichita.png",
        "chatbot_button_img": "/static/img/chatbot_button_wichita.png",
        "chatbot_background_img": "/static/img/chatbot_button_wichita.png",
        "hero_alt": "City of Wichita",
        "chatbot_name": "Wichita Assistant",
        "unified_color": "#2e4669",
        "unified_color_light": "#577cb3",
        "unified_color_dark": "#1e304a",
        "unified_color_secondary": "#FFFFFF",
        "text_color": "#FFFFFF",
    }
    TEMPLATE: ClassVar[str] = WICHITA_TEMPLATE

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
