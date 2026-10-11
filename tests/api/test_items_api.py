"""Уровень 3 — API справочника изделий и связанные правила (типы изделий, ЕИ, классификатор, удаление)."""

from sqlmodel import Session

from tests.helpers import build_food_catalog


def type_id(client, code):
    types = {t["code"]: t["id"] for t in client.get("/api/enums/types").json()}
    values = client.get(f"/api/enums/values/by-type/{types['item_type']}").json()
    return {v["code"]: v["id"] for v in values}[code]


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_reference_enums_present(client):
    codes = {t["code"] for t in client.get("/api/enums/types").json()}
    assert {"item_type", "bom_change_type"} <= codes


def test_create_item_with_type(client):
    r = client.post("/api/items/", json={"number": "API-1", "name": "Лаваш", "item_type_id": type_id(client, "detail")})
    assert r.status_code == 201
    assert r.json()["item_type_id"] == type_id(client, "detail") and r.json()["base_item_id"] is None


def test_create_item_with_foreign_enum_value_rejected(client):
    types = {t["code"]: t["id"] for t in client.get("/api/enums/types").json()}
    change_value = client.get(f"/api/enums/values/by-type/{types['bom_change_type']}").json()[0]["id"]
    r = client.post("/api/items/", json={"number": "API-2", "name": "x", "item_type_id": change_value})
    assert r.status_code == 400


def test_duplicate_number_409(client):
    client.post("/api/items/", json={"number": "API-3", "name": "x"})
    assert client.post("/api/items/", json={"number": "API-3", "name": "y"}).status_code == 409


def test_cannot_turn_item_with_spec_into_material(client, session: Session):
    cat = build_food_catalog(session)
    r = client.put(f"/api/items/{cat.id('Тесто для пиццы')}", json={"item_type_id": type_id(client, "material")})
    assert r.status_code == 400


def test_delete_component_in_use_409(client, session: Session):
    cat = build_food_catalog(session)
    r = client.delete(f"/api/items/{cat.id('Моцарелла')}")
    assert r.status_code == 409  # FK RESTRICT из item_bom


def test_delete_base_item_with_modification_409(client, session: Session):
    cat = build_food_catalog(session)
    client.post(f"/api/items/{cat.id('Комбо на двоих')}/modifications", json={"name": "Комбо XL"})
    assert client.delete(f"/api/items/{cat.id('Комбо на двоих')}").status_code == 409


def test_second_base_unit_rejected(client, session: Session):
    cat = build_food_catalog(session)
    r = client.post(
        "/api/items/units",
        json={"item_id": cat.id("Моцарелла"), "unit_simple_id": cat.unit("л").id, "is_base": True},
    )
    assert r.status_code == 409


def test_item_classifier_cycle_rejected(client, session: Session):
    cat = build_food_catalog(session)
    root, leaf = cat.classes["Продукты"].id, cat.classes["Сыры"].id
    r = client.put(f"/api/classifiers/items/{root}", json={"parent_id": leaf})
    assert r.status_code == 400
    assert client.put(f"/api/classifiers/items/{root}", json={"parent_id": 999999}).status_code == 404
