"""Уровень 1 — расчёты BomCalculator на заглушках репозиториев (без БД)."""

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from src.services.bom_calculator import BomCalculator

D = Decimal
NOW = datetime(2026, 10, 1, tzinfo=timezone.utc)


def row(rid, parent, comp, qty, for_qty="1", uq=None, is_base=True, excluded=False, order=0):
    return SimpleNamespace(id=rid, parent_item_id=parent, component_item_id=comp, quantity=D(qty),
                           for_quantity=D(for_qty), unit_quantity_id=uq, is_base=is_base,
                           is_excluded=excluded, order_number=order)


class FakeBoms:
    def __init__(self, rows):
        self.rows = rows

    def rows_at(self, parents, at):
        parents = set(parents)
        return [r for r in self.rows if r.parent_item_id in parents]


class FakeCatalog:
    def __init__(self, bases=None, classes=None, units=None):
        self.bases = bases or {}          # модификация -> базовое изделие
        self.classes = classes or {}      # изделие -> класс
        self.units = units or {}          # unit_quantity_id -> коэффициент

    def base_item_id(self, item_id):
        return self.bases.get(item_id)

    def modification_ids(self, base_id):
        return [m for m, b in self.bases.items() if b == base_id]

    def class_children(self, class_id):
        return []

    def item_info(self, ids):
        return {i: {"component_name": f"#{i}", "class_id": self.classes.get(i)} for i in ids}

    def unit_info(self, ids):
        return {i: (D(self.units[i]), "г") for i in ids if i in self.units}


# набор 1 -> 2 пиццы (2); пицца 2 -> тесто (3) 0.25; тесто 3 -> мука (4) 6 на 10; пицца -> сыр (5) 120 г
CATALOG = [row(1, 1, 2, "2"), row(2, 2, 3, "0.25"), row(3, 3, 4, "6", "10"), row(4, 2, 5, "120", uq=50)]


def test_norm_accumulates_along_path_with_unit_conversion():
    calc = BomCalculator(FakeBoms(CATALOG), FakeCatalog(units={50: "0.001"}))
    nodes = {n["component_item_id"]: n for n in calc.find_bom(1, NOW)}
    assert nodes[4]["norm"] == D("0.3")       # 2 × 0.25 × 6/10
    assert nodes[4]["path"] == [1, 2, 3, 4] and nodes[4]["lvl"] == 3
    assert nodes[5]["norm"] == D("0.24")      # 2 × 120 г × 0.001


def test_calc_bom_sums_materials_for_quantity():
    calc = BomCalculator(FakeBoms(CATALOG), FakeCatalog(units={50: "0.001"}))
    totals = {r["component_item_id"]: r["total_quantity"] for r in calc.calc_bom(1, D("10"), None, NOW)}
    assert totals == {4: D("3"), 5: D("2.4")}


def test_modification_inherits_base_rows_with_override_and_exclusion():
    rows = [row(10, 2, 3, "0.25"), row(11, 2, 5, "120"), row(12, 2, 6, "1", is_base=False),
            row(20, 7, 5, "150"), row(21, 7, 3, "0", excluded=True)]
    calc = BomCalculator(FakeBoms(rows), FakeCatalog(bases={7: 2}))
    spec = {r["component_item_id"]: r for r in calc.effective(7, NOW)}
    assert set(spec) == {5}                           # тесто исключено, строка без флага базы не наследуется
    assert spec[5]["quantity"] == D("150") and spec[5]["inherited"] is False
    base_only = calc.effective(2, NOW)
    assert {r["component_item_id"] for r in base_only} == {3, 5, 6}


def test_cycle_is_marked_and_not_expanded():
    rows = [row(1, 1, 2, "1"), row(2, 2, 1, "1")]
    calc = BomCalculator(FakeBoms(rows), FakeCatalog())
    nodes = calc.find_bom(1, NOW)
    assert [n["is_cycle"] for n in nodes] == [False, True]
    assert calc.has_cycle(1, NOW) is True


@pytest.mark.parametrize("class_id, expected", [(100, {3}), (200, {4})])
def test_calc_bom_by_class_takes_first_component_of_class_on_path(class_id, expected):
    # тесто (3) — класс 100 «полуфабрикаты», мука (4) — класс 200 «сырьё»
    calc = BomCalculator(FakeBoms(CATALOG), FakeCatalog(classes={3: 100, 4: 200}, units={50: "0.001"}))
    assert {r["component_item_id"] for r in calc.calc_bom(1, D("1"), class_id, NOW)} == expected
