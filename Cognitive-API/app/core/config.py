from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    DB_URL = os.getenv("NEON_DB_URL")
    GMAIL_USER = os.getenv("GMAIL_USER")
    GMAIL_PASS = os.getenv("GMAIL_PASS")

settings = Settings()