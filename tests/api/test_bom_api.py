"""Уровень 3 — HTTP API: каждый эндпоинт BOM, коды ответов, ошибки и граничные случаи."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from tests.helpers import build_food_catalog


@pytest.fixture()
def cat(session: Session):
    return build_food_catalog(session)


def url(cat, key, suffix=""):
    return f"/api/items/{cat.id(key)}{suffix}"


# ------------------------------------------------------------ чтение
def test_get_spec(client: TestClient, cat):
    r = client.get(url(cat, "Пицца Маргарита", "/bom"))
    assert r.status_code == 200
    body = r.json()
    assert body["item_name"] == "Пицца Маргарита"
    assert [row["component_name"] for row in body["rows"]] == [
        "Тесто для пиццы", "Соус томатный", "Моцарелла", "Базилик"
    ]


def test_get_tree(client, cat):
    r = client.get(url(cat, "Комбо на двоих", "/bom/tree"))
    assert r.status_code == 200
    nodes = r.json()["nodes"]
    assert len(nodes) == 11
    flour = next(n for n in nodes if n["component_name"] == "Мука пшеничная")
    assert flour["lvl"] == 3 and flour["norm"] == "0.300000"
    assert flour["path"][0] == cat.id("Комбо на двоих")


def test_get_norms(client, cat):
    r = client.get(url(cat, "Комбо на двоих", "/bom/norms"), params={"quantity": 10})
    assert r.status_code == 200
    rows = {x["component_name"]: x for x in r.json()["rows"]}
    assert rows["Моцарелла"]["total_quantity"] == "2.400000"
    assert rows["Моцарелла"]["base_unit_symbol"] == "кг"


def test_get_norms_by_class(client, cat):
    r = client.get(
        url(cat, "Комбо на двоих", "/bom/norms"),
        params={"quantity": 10, "class_id": cat.classes["Сыры"].id},
    )
    assert r.status_code == 200
    assert {x["component_name"] for x in r.json()["rows"]} == {"Моцарелла", "Пармезан"}


def test_spec_at_past_date(client, cat):
    t0 = client.get(url(cat, "Пицца Маргарита", "/bom")).json()["at"]
    client.put(url(cat, "Пицца Маргарита", f"/bom/{cat.id('Моцарелла')}"), json={"quantity": "150"})
    r = client.get(url(cat, "Пицца Маргарита", "/bom"), params={"at": t0})
    moz = next(x for x in r.json()["rows"] if x["component_name"] == "Моцарелла")
    assert moz["quantity"] == "120.000000"


# ------------------------------------------------------------ изменение состава
def test_add_update_replace_remove_and_history(client, cat):
    cat.item("Орегано", "material", "Специи и зелень", extra_units={"г": "0.001"})
    pizza = url(cat, "Пицца Маргарита")
    r = client.post(
        f"{pizza}/bom",
        json={"component_item_id": cat.id("Орегано"), "quantity": "2",
              "unit_quantity_id": cat.uq[("Орегано", "г")].id, "reason": "Новый рецепт"},
    )
    assert r.status_code == 201 and r.json()["component_name"] == "Орегано"

    r = client.put(f"{pizza}/bom/{cat.id('Орегано')}", json={"quantity": "3", "reason": "Уточнение"})
    assert r.status_code == 200 and r.json()["quantity"] == "3.000000"

    r = client.post(
        f"{pizza}/bom/{cat.id('Базилик')}/replace",
        json={"new_component_item_id": cat.id("Пармезан"), "quantity": "10",
              "unit_quantity_id": cat.uq[("Пармезан", "г")].id},
    )
    assert r.status_code == 200 and r.json()["component_name"] == "Пармезан"

    r = client.delete(f"{pizza}/bom/{cat.id('Орегано')}", params={"reason": "Не прижилось"})
    assert r.status_code == 204

    history = client.get(f"{pizza}/bom/changes").json()
    assert [h["change_type"] for h in history][-4:] == [
        "add_component", "change_quantity", "replace_component", "remove_component"
    ]
    assert history[-1]["reason"] == "Не прижилось"


@pytest.mark.parametrize(
    "payload",
    [
        {"component_item_id": 1, "quantity": "0"},
        {"component_item_id": 1, "quantity": "-5"},
        {"component_item_id": 1, "quantity": "1", "for_quantity": "0"},
        {"quantity": "1"},
        {"component_item_id": "abc", "quantity": "1"},
    ],
)
def test_add_validation_422(client, cat, payload):
    assert client.post(url(cat, "Пицца Маргарита", "/bom"), json=payload).status_code == 422


def test_update_without_fields_422(client, cat):
    r = client.put(url(cat, "Пицца Маргарита", f"/bom/{cat.id('Моцарелла')}"), json={"reason": "x"})
    assert r.status_code == 422


def test_errors_404(client, cat):
    assert client.get("/api/items/999999/bom").status_code == 404
    assert client.get("/api/items/999999/bom/tree").status_code == 404
    assert client.get("/api/items/999999/bom/norms").status_code == 404
    assert client.get("/api/items/999999/bom/changes").status_code == 404
    r = client.post(url(cat, "Пицца Маргарита", "/bom"), json={"component_item_id": 999999, "quantity": "1"})
    assert r.status_code == 404
    assert client.delete(url(cat, "Пицца Маргарита", f"/bom/{cat.id('Пармезан')}")).status_code == 404
    r = client.get(url(cat, "Пицца Маргарита", "/bom/norms"), params={"class_id": 999999})
    assert r.status_code == 404


def test_errors_400_and_409(client, cat):
    pizza = url(cat, "Пицца Маргарита")
    # материал не может иметь состав
    r = client.post(url(cat, "Мука пшеничная", "/bom"), json={"component_item_id": cat.id("Томаты"), "quantity": "1"})
    assert r.status_code == 400 and "материал" in r.json()["detail"]
    # цикл
    r = client.post(url(cat, "Тесто для пиццы", "/bom"), json={"component_item_id": cat.id("Пицца Маргарита"), "quantity": "1"})
    assert r.status_code == 400 and "цикл" in r.json()["detail"]
    # сам в себя
    r = client.post(f"{pizza}/bom", json={"component_item_id": cat.id("Пицца Маргарита"), "quantity": "1"})
    assert r.status_code == 400
    # дубликат
    r = client.post(f"{pizza}/bom", json={"component_item_id": cat.id("Моцарелла"), "quantity": "1"})
    assert r.status_code == 409


def test_norms_quantity_must_be_positive(client, cat):
    assert client.get(url(cat, "Пицца Маргарита", "/bom/norms"), params={"quantity": 0}).status_code == 422


def test_failed_request_is_rolled_back(client, cat):
    """Ошибка цикла возникает после вставки строки — вставка должна откатиться."""
    r = client.post(url(cat, "Тесто для пиццы", "/bom"), json={"component_item_id": cat.id("Комбо на двоих"), "quantity": "1"})
    assert r.status_code == 400
    names = [x["component_name"] for x in client.get(url(cat, "Тесто для пиццы", "/bom")).json()["rows"]]
    assert "Комбо на двоих" not in names


# ------------------------------------------------------------ модификации
def test_modifications_api(client, cat):
    r = client.post(url(cat, "Пицца Маргарита", "/modifications"), json={"name": "Маргарита острая"})
    assert r.status_code == 201
    mod = r.json()
    assert mod["base_item_id"] == cat.id("Пицца Маргарита") and mod["number"].endswith("-M1")
    lst = client.get(url(cat, "Пицца Маргарита", "/modifications")).json()
    assert [m["id"] for m in lst] == [mod["id"]]
    spec = client.get(f"/api/items/{mod['id']}/bom").json()["rows"]
    assert all(row["inherited"] for row in spec) and len(spec) == 4
    assert client.post("/api/items/999999/modifications", json={"name": "x"}).status_code == 404
    assert client.post(url(cat, "Пицца Маргарита", "/modifications"), json={"name": ""}).status_code == 422
    r = client.post(url(cat, "Пицца Маргарита", "/modifications"), json={"name": "Дубль", "number": mod["number"]})
    assert r.status_code == 409
