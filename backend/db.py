"""SQLAlchemy persistence. PostgreSQL via DATABASE_URL; SQLite for local demo."""
from __future__ import annotations
import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

def resolve_database_url(configured: str | None, *, app_env: str | None = None, is_render: bool | None = None) -> str:
    """Normalize SQLAlchemy's psycopg v3 URL and forbid ephemeral production DBs."""
    environment = (app_env if app_env is not None else os.getenv("APP_ENV", "development")).lower()
    render = bool(os.getenv("RENDER")) if is_render is None else is_render
    production = environment in {"production", "prod"} or render
    url = (configured or "sqlite:///../data/godseye.db").strip()
    if production and url.lower().startswith("sqlite"):
        raise RuntimeError("Production requires a persistent PostgreSQL DATABASE_URL; SQLite on Render is ephemeral and is disabled.")
    if production:
        try:
            parsed = make_url(url)
        except Exception as exc:
            raise RuntimeError("Production DATABASE_URL must be a valid Supabase Session Pooler PostgreSQL URL.") from exc
        if parsed.get_backend_name() not in {"postgres", "postgresql"} or not (parsed.host or "").endswith(".pooler.supabase.com") or parsed.port != 5432:
            raise RuntimeError("Production DATABASE_URL must use the Supabase Session Pooler host on port 5432 (not a direct or transaction-pooler URL).")
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    if production and url.startswith("postgresql+psycopg://") and "sslmode=" not in url:
        url += "&sslmode=require" if "?" in url else "?sslmode=require"
    return url


DATABASE_URL = resolve_database_url(os.getenv("DATABASE_URL"))
_is_sqlite = DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if _is_sqlite else {}
engine_options = {"connect_args": connect_args, "pool_pre_ping": True}
if not _is_sqlite:
    # A free Render web service runs one instance; keep the Supabase session
    # pooler footprint small and avoid creating overflow connections.
    engine_options.update(pool_size=max(1, int(os.getenv("DB_POOL_SIZE", "2"))), max_overflow=0)
engine = create_engine(DATABASE_URL, **engine_options)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

class Base(DeclarativeBase): pass

class Camera(Base):
    __tablename__="cameras"
    id: Mapped[str]=mapped_column(String(64),primary_key=True)
    name: Mapped[str]=mapped_column(String(120))
    source: Mapped[str]=mapped_column(Text)
    source_type: Mapped[str]=mapped_column(String(20),default="file")
    enabled: Mapped[bool]=mapped_column(Boolean,default=True)
    status: Mapped[str]=mapped_column(String(20),default="offline")
    city: Mapped[str|None]=mapped_column(String(80),nullable=True)
    state: Mapped[str|None]=mapped_column(String(80),nullable=True)
    country: Mapped[str|None]=mapped_column(String(80),nullable=True)
    latitude: Mapped[float|None]=mapped_column(Float,nullable=True)
    longitude: Mapped[float|None]=mapped_column(Float,nullable=True)
    feed_kind: Mapped[str]=mapped_column(String(24),default="video")
    source_url: Mapped[str|None]=mapped_column(Text,nullable=True)
    attribution: Mapped[str|None]=mapped_column(Text,nullable=True)
    refresh_seconds: Mapped[int|None]=mapped_column(Integer,nullable=True)
    last_checked_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    last_image_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    health_message: Mapped[str|None]=mapped_column(Text,nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    events: Mapped[list["Event"]]=relationship(back_populates="camera",cascade="all, delete-orphan")
    metrics: Mapped[list["CameraMetric"]]=relationship(back_populates="camera",cascade="all, delete-orphan")

class Event(Base):
    __tablename__="events"
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    camera_id: Mapped[str]=mapped_column(ForeignKey("cameras.id"),index=True)
    category: Mapped[str]=mapped_column(String(40),index=True)
    timestamp: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),index=True)
    confidence: Mapped[float]=mapped_column(Float)
    description: Mapped[str]=mapped_column(Text)
    severity: Mapped[str]=mapped_column(String(20),index=True)
    verification_status: Mapped[str]=mapped_column(String(20),default="PENDING",index=True)
    evidence_path: Mapped[str|None]=mapped_column(Text,nullable=True)
    verified_by: Mapped[str|None]=mapped_column(String(120),nullable=True)
    camera: Mapped[Camera]=relationship(back_populates="events")

class CameraMetric(Base):
    __tablename__="camera_metrics"
    id: Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    camera_id: Mapped[str]=mapped_column(ForeignKey("cameras.id"),index=True)
    timestamp: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),index=True)
    people_count: Mapped[int]=mapped_column(Integer)
    vehicle_count: Mapped[int]=mapped_column(Integer)
    crowd_density: Mapped[float]=mapped_column(Float)
    traffic_per_minute: Mapped[int]=mapped_column(Integer)
    fps: Mapped[float]=mapped_column(Float)
    camera: Mapped[Camera]=relationship(back_populates="metrics")
