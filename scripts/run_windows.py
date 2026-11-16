"""Подготовка отдельной учебной базы и обычный запуск приложения."""
import argparse
import os
import sys
import threading
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/mispris_lab7_demo")


def main():
    import psycopg2
    from psycopg2 import sql
    from sqlalchemy.engine import make_url
    from sqlalchemy import text
    from alembic import command
    from alembic.config import Config
    from src.database.database import SessionLocal
    from data.seed import seed

    parser = argparse.ArgumentParser()
    parser.add_argument("--init-only", action="store_true")
    args = parser.parse_args()
    url = make_url(os.environ["DATABASE_URL"])
    if not url.database or not url.database.startswith("mispris_lab7_"):
        raise RuntimeError("Укажите отдельную учебную БД mispris_lab7_*. Рабочая БД предыдущих работ не используется.")
    connection = psycopg2.connect(host=url.host or "localhost", port=url.port or 5432,
                                 user=url.username, password=url.password, dbname="postgres")
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname=%s", (url.database,))
            if not cursor.fetchone():
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(url.database)))
    finally:
        connection.close()
    command.upgrade(Config("alembic.ini"), "head")
    with SessionLocal() as session:
        if session.execute(text("SELECT count(*) FROM item")).scalar_one() == 0:
            seed(session)
            session.commit()
            print("Учебные данные загружены.")
        else:
            print("Используются сохранённые данные учебной базы.")
    if args.init_only:
        return
    port = int(os.environ.get("APP_PORT", "8007"))
    print(f"Приложение: http://localhost:{port}/docs/lab7\nДля остановки нажмите Ctrl+C.")
    threading.Timer(2, lambda: webbrowser.open(f"http://localhost:{port}/docs/lab7")).start()
    import uvicorn
    uvicorn.run("src.main:app", host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
