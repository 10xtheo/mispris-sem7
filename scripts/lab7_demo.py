"""Создание и восстановление отдельного стенда №7. Рабочую БД не использует."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
DATABASE = "mispris_lab7_demo"
URL = f"postgresql+psycopg2://postgres:postgres@localhost:5432/{DATABASE}"
os.environ["DATABASE_URL"] = URL


def main():
    import psycopg2
    from psycopg2 import sql
    from alembic import command
    from alembic.config import Config
    from src.database.database import SessionLocal
    from data.seed import seed
    connection = psycopg2.connect(host="localhost", user="postgres", password="postgres", dbname="postgres")
    connection.autocommit = True
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_database WHERE datname=%s", (DATABASE,))
        if not cursor.fetchone():
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DATABASE)))
    connection.close()
    config = Config("alembic.ini")
    config.attributes["sqlalchemy.url"] = URL
    command.upgrade(config, "head")
    with SessionLocal() as session:
        seed(session)
        session.commit()
    print(f"Демонстрационная БД {DATABASE} восстановлена")


if __name__ == "__main__":
    main()
