from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String

from sqlalchemy.pool import StaticPool

DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
)

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String),
)


def create_tables() -> None:
    """Create all tables if they don't exist yet."""
    metadata.create_all(engine)
