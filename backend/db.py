"""SQLAlchemy persistence. PostgreSQL via DATABASE_URL; SQLite for local demo."""
from __future__ import annotations
import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///../data/godseye.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
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
