"""Уровень 2 — SQL-функции и ограничения БД (effective_bom, find_bom, calc_bom, bom_has_cycle)."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from src.models.bom import ItemBom
from src.repository.bom_repository import ItemBomRepository
from tests.helpers import build_food_catalog

D = Decimal


def now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture()
def cat(session: Session):
    return build_food_catalog(session)


@pytest.fixture()
def repo(session: Session) -> ItemBomRepository:
    return ItemBomRepository(session)


def by_name(rows, key="component_name"):
    return {r[key]: r for r in rows}


# ------------------------------------------------------------ effective_bom
def test_effective_bom_one_level_in_order(cat, repo):
    rows = repo.effective(cat.id("Пицца Маргарита"), now())
    assert [r["component_name"] for r in rows] == ["Тесто для пиццы", "Соус томатный", "Моцарелла", "Базилик"]
    assert all(not r["inherited"] for r in rows)
    moz = by_name(rows)["Моцарелла"]
    assert moz["quantity"] == D("120") and moz["unit_symbol"] == "г" and moz["base_unit_symbol"] == "кг"


def test_effective_bom_of_material_is_empty(cat, repo):
    assert repo.effective(cat.id("Мука пшеничная"), now()) == []


# ------------------------------------------------------------ find_bom (FIND_BOM)
def test_find_bom_full_depth_and_levels(cat, repo):
    nodes = repo.find_bom(cat.id("Комбо на двоих"), now())
    levels = {(n["component_name"], n["lvl"]) for n in nodes}
    assert ("Пицца Маргарита", 1) in levels
    assert ("Тесто для пиццы", 2) in levels
    assert ("Мука пшеничная", 3) in levels
    assert ("Базилик", 3) in levels and ("Базилик", 2) in levels  # базилик и в пицце, и в соусе
    assert max(n["lvl"] for n in nodes) == 3
    assert len(nodes) == 11  # пицца(1) + её дерево(9) + пармезан(1)
    assert not any(n["is_cycle"] for n in nodes)


def test_find_bom_accumulates_norm_with_unit_conversion(cat, repo):
    nodes = repo.find_bom(cat.id("Комбо на двоих"), now())
    norms = {(n["component_name"], n["lvl"]): n["norm"] for n in nodes}
    assert norms[("Пицца Маргарита", 1)] == D("2")
    assert norms[("Тесто для пиццы", 2)] == D("0.5")
    assert norms[("Мука пшеничная", 3)] == pytest.approx(D("0.3"))
    assert norms[("Дрожжи", 3)] == pytest.approx(D("0.01"))  # 20 г × 0.001 × 0.5
    assert norms[("Моцарелла", 2)] == pytest.approx(D("0.24"))
    assert norms[("Базилик", 3)] == pytest.approx(D("0.0016"))  # 100 г / 10 кг соуса × 0.16 кг
    assert norms[("Пармезан", 1)] == pytest.approx(D("0.03"))


def test_find_bom_path_is_depth_first(cat, repo):
    nodes = repo.find_bom(cat.id("Пицца Маргарита"), now())
    names = [n["component_name"] for n in nodes]
    assert names == [
        "Тесто для пиццы", "Мука пшеничная", "Вода питьевая", "Дрожжи",
        "Соус томатный", "Томаты", "Базилик",
        "Моцарелла", "Базилик",
    ]


# ------------------------------------------------------------ calc_bom (CALC_BOM)
def test_calc_bom_all_materials_for_quantity(cat, repo):
    rows = by_name(repo.calc_bom(cat.id("Комбо на двоих"), D("10"), None, now()))
    assert set(rows) == {
        "Мука пшеничная", "Вода питьевая", "Дрожжи", "Томаты", "Базилик", "Моцарелла", "Пармезан"
    }
    assert rows["Мука пшеничная"]["total_quantity"] == pytest.approx(D("3"))
    assert rows["Вода питьевая"]["total_quantity"] == pytest.approx(D("1.9"))
    assert rows["Вода питьевая"]["base_unit_symbol"] == "л"
    assert rows["Томаты"]["total_quantity"] == pytest.approx(D("1.92"))
    assert rows["Базилик"]["total_quantity"] == pytest.approx(D("0.116"))  # сумма по двум путям
    assert rows["Моцарелла"]["total_quantity"] == pytest.approx(D("2.4"))


def test_calc_bom_by_class_includes_subclasses(cat, repo):
    cls_id = cat.classes["Молочные продукты"].id  # «Сыры» — подкласс
    rows = by_name(repo.calc_bom(cat.id("Комбо на двоих"), D("10"), cls_id, now()))
    assert set(rows) == {"Моцарелла", "Пармезан"}
    assert rows["Пармезан"]["total_quantity"] == pytest.approx(D("0.3"))


def test_calc_bom_by_class_of_semi_products_does_not_double_count(cat, repo):
    cls_id = cat.classes["Продукты"].id  # корневой класс: берётся первый компонент класса на пути
    rows = by_name(repo.calc_bom(cat.id("Комбо на двоих"), D("1"), cls_id, now()))
    assert set(rows) == {"Пицца Маргарита", "Пармезан"}
    semi = by_name(repo.calc_bom(cat.id("Комбо на двоих"), D("10"), cat.classes["Полуфабрикаты"].id, now()))
    assert semi["Тесто для пиццы"]["total_quantity"] == pytest.approx(D("5"))
    assert semi["Соус томатный"]["total_quantity"] == pytest.approx(D("1.6"))
    assert "Мука пшеничная" not in semi


# ------------------------------------------------------------ время и версии
def test_versions_give_state_at_date(cat, repo, session):
    before = now()
    row = session.get(ItemBom, repo.effective_row(cat.id("Пицца Маргарита"), cat.id("Моцарелла"), before)["bom_id"])
    t = now()
    repo.close(row, t)
    repo.create({
        "parent_item_id": row.parent_item_id, "component_item_id": row.component_item_id,
        "quantity": D("150"), "for_quantity": D("1"), "unit_quantity_id": row.unit_quantity_id,
        "order_number": row.order_number, "valid_from": t,
    })
    assert repo.effective_row(cat.id("Пицца Маргарита"), cat.id("Моцарелла"), before)["quantity"] == D("120")
    assert repo.effective_row(cat.id("Пицца Маргарита"), cat.id("Моцарелла"), now())["quantity"] == D("150")


# ------------------------------------------------------------ циклы и ограничения
def test_cycle_is_detected_without_infinite_recursion(cat, repo):
    # Соус -> Пицца при Пицца -> Соус: обходим ограничения сервиса, пишем напрямую
    repo.create({
        "parent_item_id": cat.id("Соус томатный"), "component_item_id": cat.id("Пицца Маргарита"),
        "quantity": D("1"), "valid_from": now(),
    })
    assert repo.has_cycle(cat.id("Пицца Маргарита"), now()) is True
    nodes = repo.find_bom(cat.id("Пицца Маргарита"), now())
    assert any(n["is_cycle"] for n in nodes)  # обход завершился и пометил цикл


def test_no_cycle_in_valid_catalog(cat, repo):
    assert repo.has_cycle(cat.id("Комбо на двоих"), now()) is False


@pytest.mark.parametrize(
    "values",
    [
        {"component": "Пицца Маргарита", "quantity": "1"},       # сам в себя
        {"component": "Моцарелла", "quantity": "0"},             # нулевой расход
        {"component": "Моцарелла", "quantity": "1", "for_quantity": "0"},
        {"component": "Моцарелла", "quantity": "1"},             # вторая действующая строка
    ],
)
def test_db_constraints(cat, repo, session, values):
    data = {
        "parent_item_id": cat.id("Пицца Маргарита"),
        "component_item_id": cat.id(values["component"]),
        "quantity": D(values["quantity"]),
        "for_quantity": D(values.get("for_quantity", "1")),
        "valid_from": now(),
    }
    with pytest.raises(IntegrityError):
        with session.begin_nested():
            repo.create(data)
