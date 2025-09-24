"""
Inicialização do banco (SQLAlchemy 2.x)
"""

from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from ..core.config import settings


class Base(DeclarativeBase):
    pass


_engine_kwargs = {"connect_args": {"check_same_thread": False}} if settings.DB_URL.startswith("sqlite") else {}
engine = create_engine(settings.DB_URL, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db():
    from . import models  # importa para registrar mapeamentos
    Base.metadata.create_all(bind=engine)


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
