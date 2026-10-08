from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    database_url: str = "sqlite:///./ovqatbot.db"

    # Telegram
    telegram_bot_token: str = ""
    webapp_url: str = ""
    # initData amal qilish muddati (soniya)
    init_data_max_age: int = 86400

    # DEV_MODE=true bo'lsa Telegram imzosisiz "mehmon" foydalanuvchi bilan ishlaydi
    dev_mode: bool = False

    # Gemini API (https://aistudio.google.com/apikey). Kalit bo'lmasa qoidaga asoslangan parser
    # va tayyor retseptlar ishlaydi.
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    llm_enabled: bool = True

    # n8n / tashqi avtomatlashtirish uchun retsept yuklash endpointi
    admin_token: str = ""

    cors_origins: str = "*"


settings = Settings()
