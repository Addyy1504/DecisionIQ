import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

backend_env = BASE_DIR / ".env"
root_env = PROJECT_DIR / ".env"

if backend_env.exists():
    load_dotenv(backend_env)
elif root_env.exists():
    load_dotenv(root_env)
else:
    raise FileNotFoundError(
        "No .env file found in backend/ or project root."
    )


DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME")


if not DB_USER:
    raise ValueError("DB_USER is missing from .env")

if not DB_PASSWORD:
    raise ValueError("DB_PASSWORD is missing from .env")

if not DB_NAME:
    raise ValueError("DB_NAME is missing from .env")


connection_url = URL.create(
    drivername="mysql+mysqlconnector",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME
)


engine = create_engine(
    connection_url,
    pool_pre_ping=True
)


def test_connection():
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT DATABASE();")
        )

        return result.scalar()