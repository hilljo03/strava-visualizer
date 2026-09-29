from sqlalchemy import (
    create_engine,
    MetaData,
    DateTime,
    Table,
    Column,
    Integer,
    String,
    BigInteger,
    DateTime,
    Float,
)
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
    Column("strava_athlete_id", BigInteger, unique=True, nullable=False),
    Column("username", String),
    Column("strava_access_token", String, nullable=True),
    Column("strava_refresh_token", String, nullable=True),
    Column("strava_token_expires_at", BigInteger, nullable=True),
)

activities = Table(
    "activities",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("strava_athlete_id", BigInteger, nullable=False, index=True),
    Column("activity", String(50), nullable=False),
    Column("start_date_local", DateTime, nullable=False),
    Column("start_lat", Float, nullable=True),
    Column("start_long", Float, nullable=True),
    Column("avg_heartrate", Float, nullable=True),
    Column("max_heartrate", Float, nullable=True),
    Column("suffer_score", Integer, nullable=True),
    Column("strava_activity_id", BigInteger, nullable=False),
    Column("polyline", String, nullable=True),
)


def create_tables() -> None:
    """Create all tables if they don't exist yet."""
    metadata.create_all(engine)
