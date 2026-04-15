"""
SQLAlchemy async ORM models — Alembic-compatible, Supabase/RDS-ready.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Float, Integer, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    preferences: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    itineraries: Mapped[list["Itinerary"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Itinerary(Base):
    __tablename__ = "itineraries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    destination: Mapped[str] = mapped_column(String(255))
    num_days: Mapped[int] = mapped_column(Integer)
    budget_usd: Mapped[float] = mapped_column(Float)
    total_cost_usd: Mapped[float] = mapped_column(Float)
    travel_style: Mapped[Optional[str]] = mapped_column(String(50))
    itinerary_data: Mapped[dict] = mapped_column(JSON)
    reasoning: Mapped[Optional[str]] = mapped_column(Text)
    weather_summary: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[Optional["User"]] = relationship(back_populates="itineraries")
