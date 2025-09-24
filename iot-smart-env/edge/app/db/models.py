"""
Modelos SQLAlchemy:
- Reading: leituras dos sensores
- Rule: regras de automação (thresholds, etc.)
- ActionLog: log de ações disparadas por regras
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    node_id: Mapped[str] = mapped_column(String(64), index=True)
    temperature_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    humidity_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    soil_moisture_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    motion: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    raw_json: Mapped[str] = mapped_column(Text, nullable=False)


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    # Definição simples de regra do tipo threshold/operador
    metric: Mapped[str] = mapped_column(String(64))  # ex: temperature_c | humidity_pct | soil_moisture_pct
    operator: Mapped[str] = mapped_column(String(8))  # <, <=, >, >=, ==, !=
    value: Mapped[float] = mapped_column(Float)
    action: Mapped[str] = mapped_column(String(64))   # ex: "irrigation_on", "notify"
    action_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    logs: Mapped[list["ActionLog"]] = relationship(back_populates="rule")


class ActionLog(Base):
    __tablename__ = "action_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("rules.id", ondelete="SET NULL"), nullable=True, index=True)
    reading_id: Mapped[int] = mapped_column(ForeignKey("readings.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(64))
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    rule: Mapped[Optional["Rule"]] = relationship(back_populates="logs")
