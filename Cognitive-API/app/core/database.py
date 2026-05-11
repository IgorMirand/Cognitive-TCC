import psycopg2
from .config import settings

def get_db_connection():
    if not settings.DB_URL:
        raise Exception("NEON_DB_URL não configurada.")
    return psycopg2.connect(settings.DB_URL)
