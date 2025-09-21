from pydantic import BaseSettings, AnyUrl

class Settings(BaseSettings):
    TELEGRAM_API_ID: int
    TELEGRAM_API_HASH: str
    TELEGRAM_SESSION: str = "eumenides_session"
    DATABASE_URL: AnyUrl
    POLL_INTERVAL_SECONDS: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
