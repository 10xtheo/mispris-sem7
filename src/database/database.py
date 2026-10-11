from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

from src.config.config import settings

engine = create_engine(settings.DATABASE_URL, echo=settings.SQL_ECHO)

SessionLocal = sessionmaker(bind=engine, class_=Session, autocommit=False, autoflush=False)


def get_session() -> Generator[Session, None, None]:
    """Сессия на один HTTP-запрос: commit при успехе, rollback при любой ошибке."""
    with SessionLocal() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
