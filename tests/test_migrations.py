"""Миграции Alembic: чистая БД -> head -> base -> head, схема совпадает с моделями."""

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlmodel import SQLModel

import src.models  # noqa: F401  — регистрация всех таблиц в metadata
from tests.conftest import TEST_DATABASE_URL, alembic_config, recreate_database

MIGR_URL = make_url(TEST_DATABASE_URL).set(database=make_url(TEST_DATABASE_URL).database + "_migr")
MIGR_URL_STR = MIGR_URL.render_as_string(hide_password=False)


def test_upgrade_downgrade_upgrade():
    recreate_database(MIGR_URL_STR)
    cfg = alembic_config(MIGR_URL_STR)
    engine = create_engine(MIGR_URL_STR)
    try:
        command.upgrade(cfg, "002")
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO item (number, name) VALUES ('LEGACY', 'Legacy item')"))
        command.upgrade(cfg, "head")
        tables = set(inspect(engine).get_table_names())
        assert {"item_bom", "item_change", "unit_simple", "technology_operation", "technology_input"} <= tables
        assert "unit_simple_id" not in tables  # таблица переименована
        with engine.connect() as connection:
            assert connection.execute(text("SELECT name FROM item WHERE number = 'LEGACY'")).scalar_one() == "Legacy item"
            assert connection.execute(text("SELECT to_regprocedure('mr_q(integer,double precision)') IS NOT NULL")).scalar_one()

        command.downgrade(cfg, "002")
        assert "technology_operation" not in inspect(engine).get_table_names()
        with engine.connect() as connection:
            assert connection.execute(text("SELECT to_regprocedure('find_tm(integer)') IS NULL")).scalar_one()
            assert connection.execute(text("SELECT name FROM item WHERE number = 'LEGACY'")).scalar_one() == "Legacy item"
        command.downgrade(cfg, "001")
        tables = set(inspect(engine).get_table_names())
        assert "item_bom" not in tables and "item_change" not in tables

        command.downgrade(cfg, "base")
        command.upgrade(cfg, "head")
        assert "item_bom" in set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_models_match_migrations():
    """Autogenerate не должен находить расхождений между моделями и схемой после миграций."""
    engine = create_engine(TEST_DATABASE_URL)
    try:
        with engine.connect() as conn:
            diff = compare_metadata(MigrationContext.configure(conn), SQLModel.metadata)
    finally:
        engine.dispose()
    # Индексы/ограничения, которые описаны только в миграции, сравниваем мягко: важны таблицы и колонки
    significant = [d for d in diff if d[0] in ("add_table", "remove_table", "add_column", "remove_column")]
    assert significant == []


def test_rule_migration_preserves_legacy_function_and_constraint():
    import json
    url=make_url(TEST_DATABASE_URL).set(database=make_url(TEST_DATABASE_URL).database+"_rules_migr").render_as_string(hide_password=False)
    recreate_database(url)
    cfg=alembic_config(url)
    engine=create_engine(url)
    definition={"parameters":{"x":"number"},"result":"bool","body":{"kind":"op","op":"ge","args":[{"kind":"param","name":"x"},{"kind":"const","value":30}]}}
    expression={"kind":"call","function":"LegacyFun","args":{"x":{"kind":"param","name":"diameter"}}}
    try:
        command.upgrade(cfg,"004")
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO item(id,number,name) VALUES(999,'OLD-7','Legacy template')"))
            connection.execute(text("INSERT INTO configuration_function(id,code,name,definition) VALUES(999,'LegacyFun','Legacy',CAST(:d AS jsonb))"),{"d":json.dumps(definition)})
            connection.execute(text("INSERT INTO configuration_constraint(id,template_id,name,expression) VALUES(999,999,'Legacy',CAST(:d AS jsonb))"),{"d":json.dumps(expression)})
        command.upgrade(cfg,"005")
        with engine.connect() as connection:
            assert connection.execute(text("SELECT count(*) FROM rule_formal_argument WHERE function_id=999")).scalar_one()==1
            assert connection.execute(text("SELECT count(*) FROM rule_constraint_root WHERE constraint_id=999")).scalar_one()==1
        command.downgrade(cfg,"004")
        with engine.connect() as connection:
            assert connection.execute(text("SELECT definition FROM configuration_function WHERE id=999")).scalar_one()==definition
            assert connection.execute(text("SELECT expression FROM configuration_constraint WHERE id=999")).scalar_one()==expression
        command.upgrade(cfg,"005")
    finally:
        engine.dispose()
