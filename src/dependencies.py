from typing import Generator
from sqlalchemy import Connection
from src.database import engine


def get_db() -> Generator[Connection, None, None]:
    with engine.connect() as conn:
        yield conn
