from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    DB_URL: str = os.getenv("NEON_DB_URL", "")
    GMAIL_USER: str = os.getenv("GMAIL_USER", "")
    GMAIL_PASS: str = os.getenv("GMAIL_PASS", "")

    # API Key global — defina no .env como: API_KEY=
    API_KEY: str = os.getenv("API_KEY", "")

    # JWT — defina no .env como: JWT_SECRET=
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24


settings = Settings()
