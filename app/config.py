from openai import OpenAI
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    ZILLIZ_AUTH_TOKEN: str
    ZILLIZ_URL: str
    PORT: int = 8000

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def client(self) -> OpenAI:
        return OpenAI(api_key=self.OPENAI_API_KEY)

settings = Settings()
