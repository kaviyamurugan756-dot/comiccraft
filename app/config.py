from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "ComicCraft - AI Comic Story Creator"
    gemini_api_key: str = ""
    gemini_flash_model: str = "gemini-2.5-flash"
    gemini_pro_model: str = "gemini-2.5-pro"
    hf_token: str = ""
    hf_image_model: str = "black-forest-labs/FLUX.1-schnell"
    image_provider: str = "huggingface"
    mock_ai: bool = False
    panels: int = 5
    output_dir: str = "static"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
