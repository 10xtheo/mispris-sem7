"""Общие фикстуры тестов.

Тесты работают с отдельной БД (TEST_DATABASE_URL, по умолчанию mispis_sem7_test).
БД пересоздаётся один раз на прогон, схема накатывается миграциями Alembic
(тем самым миграции тоже проверяются). Каждый тест выполняется в транзакции,
которая откатывается после теста, поэтому тесты независимы друг от друга.
"""

import os
from pathlib import Path
from typing import Generator

import pytest
from dotenv import dotenv_values
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parent.parent
_env = dotenv_values(ROOT / ".env")
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or _env.get("TEST_DATABASE_URL") or (
    "postgresql+psycopg2://postgres:postgres@localhost:5432/mispis_sem7_test"
)
# Приложение и Alembic должны смотреть в тестовую БД — задаём до импорта src.*
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import psycopg2  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session  # noqa: E402

from src.database.database import engine, get_session  # noqa: E402
from src.main import app  # noqa: E402


def recreate_database(url: str) -> None:
    u = make_url(url)
    conn = psycopg2.connect(
        host=u.host, port=u.port or 5432, user=u.username, password=u.password, dbname="postgres"
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(f'DROP DATABASE IF EXISTS "{u.database}" WITH (FORCE)')
        cur.execute(f'CREATE DATABASE "{u.database}"')
    conn.close()


def alembic_config(url: str) -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    cfg.attributes["sqlalchemy.url"] = url
    return cfg


@pytest.fixture(scope="session", autouse=True)
def test_database() -> Generator[None, None, None]:
    recreate_database(TEST_DATABASE_URL)
    command.upgrade(alembic_config(TEST_DATABASE_URL), "head")
    yield
    engine.dispose()


@pytest.fixture()
def session() -> Generator[Session, None, None]:
    """Сессия внутри внешней транзакции; commit() приложения фиксирует лишь SAVEPOINT."""
    connection = engine.connect()
    outer = connection.begin()
    sess = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield sess
    finally:
        sess.close()
        outer.rollback()
        connection.close()


@pytest.fixture()
def client(session: Session) -> Generator[TestClient, None, None]:
    def override_get_session() -> Generator[Session, None, None]:
        # Как в приложении: запрос атомарен. SAVEPOINT вместо commit, чтобы ошибка
        # запроса откатывала только его изменения, а не данные, подготовленные тестом.
        nested = session.begin_nested()
        try:
            yield session
            nested.commit()
        except Exception:
            nested.rollback()
            raise

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
