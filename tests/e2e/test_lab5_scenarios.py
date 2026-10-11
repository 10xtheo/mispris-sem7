"""Уровень 4 — сквозные сценарии задания №5 только через HTTP API (как на защите).

Каждый тест соответствует пункту требований (слайд 3 «Задание №5»):
    Т1 Ведение справочника изделий с типами (материал, деталь, СЕ, комплекс)
    Т2 Формирование спецификаций с нормами расхода
    Т3 Управление изменениями (история)
    Т4 Модификации на основе базовых изделий
    Т5 Анализ состава на всю глубину вложенности (FIND_BOM)
    Т6 Сводные нормы расхода материалов заданного класса (CALC_BOM)
"""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

D = Decimal


class Api:
    """Тонкая обёртка над API для сценариев."""

    def __init__(self, client: TestClient):
        self.c = client
        types = {t["code"]: t["id"] for t in self.ok(self.c.get("/api/enums/types"))}
        values = self.ok(self.c.get(f"/api/enums/values/by-type/{types['item_type']}"))
        self.types = {v["code"]: v["id"] for v in values}
        self.units: dict[str, int] = {}
        self._n = 0

    @staticmethod
    def ok(r, status=200):
        assert r.status_code == status, (r.status_code, r.text)
        return r.json() if r.content else None

    def unit(self, symbol, code):
        if symbol not in self.units:
            self.units[symbol] = self.ok(
                self.c.post("/api/units/", json={"code": code, "name": symbol, "cond_symbol_1": symbol}), 201
            )["id"]
        return self.units[symbol]

    def cls(self, name, parent=None):
        return self.ok(self.c.post("/api/classifiers/items", json={"name": name, "parent_id": parent}), 201)["id"]

    def item(self, name, type_code, class_id, base_unit=("кг", "KGM"), grams=False):
        self._n += 1
        it = self.ok(
            self.c.post(
                "/api/items/",
                json={"number": f"E2E-{self._n:02d}", "name": name,
                      "item_type_id": self.types[type_code], "item_class_id": class_id},
            ),
            201,
        )
        self.ok(self.c.post("/api/items/units", json={
            "item_id": it["id"], "unit_simple_id": self.unit(*base_unit), "is_base": True}), 201)
        if grams:
            it["g"] = self.ok(self.c.post("/api/items/units", json={
                "item_id": it["id"], "unit_simple_id": self.unit("г", "GRM"), "coefficient": "0.001"}), 201)["id"]
        return it

    def add(self, parent, comp, qty, unit=None, for_qty="1", order=0, is_base=True):
        return self.ok(self.c.post(f"/api/items/{parent['id']}/bom", json={
            "component_item_id": comp["id"], "quantity": qty, "for_quantity": for_qty,
            "unit_quantity_id": unit, "order_number": order, "is_base": is_base}), 201)

    def spec(self, item, **params):
        return {r["component_name"]: r for r in self.ok(self.c.get(f"/api/items/{item['id']}/bom", params=params))["rows"]}

    def tree(self, item):
        return self.ok(self.c.get(f"/api/items/{item['id']}/bom/tree"))["nodes"]

    def norms(self, item, qty, class_id=None):
        params = {"quantity": qty}
        if class_id:
            params["class_id"] = class_id
        rows = self.ok(self.c.get(f"/api/items/{item['id']}/bom/norms", params=params))["rows"]
        return {r["component_name"]: D(r["total_quantity"]) for r in rows}


@pytest.fixture()
def world(client):
    """Каталог сервиса доставки еды, созданный через API."""
    api = Api(client)
    products = api.cls("Продукты")
    raw = api.cls("Сырьё", products)
    w = {"api": api, "cls": {}}
    w["cls"]["Сыры"] = api.cls("Сыры", api.cls("Молочные продукты", raw))
    w["cls"]["Овощи"] = api.cls("Овощи", raw)
    w["cls"]["Мука"] = api.cls("Мука и крупы", raw)
    w["cls"]["Полуфабрикаты"] = api.cls("Полуфабрикаты", products)
    dishes = api.cls("Блюда", products)
    sets = api.cls("Наборы", products)

    w["flour"] = api.item("Мука пшеничная", "material", w["cls"]["Мука"])
    w["tomato"] = api.item("Томаты", "material", w["cls"]["Овощи"])
    w["mozz"] = api.item("Моцарелла", "material", w["cls"]["Сыры"], grams=True)
    w["parm"] = api.item("Пармезан", "material", w["cls"]["Сыры"], grams=True)
    w["jalap"] = api.item("Халапеньо", "material", w["cls"]["Овощи"], grams=True)
    w["dough"] = api.item("Тесто для пиццы", "detail", w["cls"]["Полуфабрикаты"])
    w["sauce"] = api.item("Соус томатный", "detail", w["cls"]["Полуфабрикаты"])
    w["pizza"] = api.item("Пицца Маргарита", "assembly", dishes, base_unit=("шт", "PCE"))
    w["combo"] = api.item("Комбо на двоих", "complex", sets, base_unit=("шт", "PCE"))

    api.add(w["dough"], w["flour"], "0.6")
    api.add(w["sauce"], w["tomato"], "1.2")
    api.add(w["pizza"], w["dough"], "0.25", order=1)
    api.add(w["pizza"], w["sauce"], "0.08", order=2)
    api.add(w["pizza"], w["mozz"], "120", unit=w["mozz"]["g"], order=3)
    api.add(w["combo"], w["pizza"], "2", order=1)
    api.add(w["combo"], w["parm"], "30", unit=w["parm"]["g"], order=2)
    return w


def test_T1_item_types(world):
    api = world["api"]
    assert world["flour"]["item_type_id"] == api.types["material"]
    assert world["dough"]["item_type_id"] == api.types["detail"]
    assert world["pizza"]["item_type_id"] == api.types["assembly"]
    assert world["combo"]["item_type_id"] == api.types["complex"]
    # материал — лист дерева: своего состава не имеет
    r = api.c.post(f"/api/items/{world['flour']['id']}/bom", json={"component_item_id": world["tomato"]["id"], "quantity": "1"})
    assert r.status_code == 400


def test_T2_specification_with_norms(world):
    spec = world["api"].spec(world["pizza"])
    assert list(spec) == ["Тесто для пиццы", "Соус томатный", "Моцарелла"]
    assert spec["Моцарелла"]["quantity"] == "120.000000" and spec["Моцарелла"]["unit_symbol"] == "г"
    assert spec["Тесто для пиццы"]["for_quantity"] == "1.000000"


def test_T3_change_management(world):
    api, pizza, mozz = world["api"], world["pizza"], world["mozz"]
    before = api.ok(api.c.get(f"/api/items/{pizza['id']}/bom"))["at"]
    api.ok(api.c.put(f"/api/items/{pizza['id']}/bom/{mozz['id']}", json={"quantity": "150", "reason": "Отзывы клиентов"}))
    history = api.ok(api.c.get(f"/api/items/{pizza['id']}/bom/changes"))
    last = history[-1]
    assert last["change_type"] == "change_quantity" and last["reason"] == "Отзывы клиентов"
    assert (last["old"]["quantity"], last["new"]["quantity"]) == ("120.000000", "150.000000")
    assert api.spec(pizza, at=before)["Моцарелла"]["quantity"] == "120.000000"
    assert api.spec(pizza)["Моцарелла"]["quantity"] == "150.000000"


def test_T4_modifications(world):
    api, pizza = world["api"], world["pizza"]
    mod = api.ok(api.c.post(f"/api/items/{pizza['id']}/modifications", json={"name": "Маргарита острая"}), 201)
    api.ok(api.c.put(f"/api/items/{mod['id']}/bom/{world['mozz']['id']}", json={"quantity": "150"}))
    api.ok(api.c.post(f"/api/items/{mod['id']}/bom", json={
        "component_item_id": world["jalap"]["id"], "quantity": "30", "unit_quantity_id": world["jalap"]["g"]}), 201)
    api.ok(api.c.delete(f"/api/items/{mod['id']}/bom/{world['sauce']['id']}"), 204)

    mod_spec = api.spec(mod)
    assert set(mod_spec) == {"Тесто для пиццы", "Моцарелла", "Халапеньо"}
    assert mod_spec["Тесто для пиццы"]["inherited"] is True
    assert api.spec(pizza)["Моцарелла"]["quantity"] == "120.000000"  # база не тронута
    # изменение базового изделия видно в модификации
    api.ok(api.c.put(f"/api/items/{pizza['id']}/bom/{world['dough']['id']}", json={"quantity": "0.3"}))
    assert api.spec(mod)["Тесто для пиццы"]["quantity"] == "0.300000"
    n = api.norms(mod, "10")
    assert n["Моцарелла"] == D("1.5") and n["Халапеньо"] == D("0.3") and "Томаты" not in n


def test_T5_full_depth_structure(world):
    nodes = world["api"].tree(world["combo"])
    by_name = {n["component_name"]: n for n in nodes}
    assert by_name["Пицца Маргарита"]["lvl"] == 1
    assert by_name["Тесто для пиццы"]["lvl"] == 2
    assert by_name["Мука пшеничная"]["lvl"] == 3
    assert by_name["Мука пшеничная"]["norm"] == "0.300000"  # 2 × 0.25 × 0.6
    assert len(nodes) == 7


def test_T6_summary_norms_by_class(world):
    api = world["api"]
    all_materials = api.norms(world["combo"], "10")
    assert all_materials == {
        "Мука пшеничная": D("3.000000"),
        "Томаты": D("1.920000"),
        "Моцарелла": D("2.400000"),
        "Пармезан": D("0.300000"),
    }
    cheese = api.norms(world["combo"], "10", world["cls"]["Сыры"])
    assert cheese == {"Моцарелла": D("2.400000"), "Пармезан": D("0.300000")}
    semi = api.norms(world["combo"], "10", world["cls"]["Полуфабрикаты"])
    assert semi == {"Тесто для пиццы": D("5.000000"), "Соус томатный": D("1.600000")}
