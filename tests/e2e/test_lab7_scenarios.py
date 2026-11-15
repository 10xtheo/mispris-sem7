"""Сквозные испытания №7: метаданные → ограничение → вариант → заказ."""
from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import select

from src.models.enums import EnumType, EnumValue
from src.models.parameters import Parameter
from src.models.items import Item
from src.models.configuration import CustomerOrderPosition, VariantParameterValue
from tests.helpers import Catalog
from tests.unit.test_constraint_interpreter import call, const, op, param

ROOT = "/api/configuration"


@pytest.fixture
def configurator(session, client):
    catalog = Catalog(session)
    catalog.cls("Пиццы")
    item = catalog.item("Пицца по заказу", "assembly", cls="Пиццы", base_unit="шт")
    enum = EnumType(code="param_type", name="Тип параметра")
    session.add(enum)
    session.flush()
    typ = EnumValue(enum_type_id=enum.id, order_number=1, code="number", name="Число")
    session.add(typ)
    session.flush()
    parameter = Parameter(code="diameter", name="Диаметр", param_type_id=typ.id)
    session.add(parameter)
    session.flush()
    response = client.post(f"{ROOT}/classes/{item.item_class_id}/parameters", json={
        "parameter_id": parameter.id, "min_value": 20, "max_value": 40})
    assert response.status_code == 201, response.text
    assert client.put(f"{ROOT}/items/{item.id}/configurator").status_code == 200
    return item


def test_full_configuration_to_agreed_order(client, configurator):
    item = configurator
    params = client.get(f"{ROOT}/items/{item.id}/parameters").json()
    assert params[0]["code"] == "diameter"
    assert client.post(f"{ROOT}/functions", json={"code": "fits", "name": "Допустимый диаметр",
        "definition": {"parameters": {"d": "number"}, "result": "bool",
                       "body": op("le", param("d"), const(35))}}).status_code == 201
    rule = {"name": "Ограничение печи", "expression": call("fits", d=param("diameter"))}
    assert client.post(f"{ROOT}/items/{item.id}/constraints", json=rule).status_code == 201
    rejected = client.post(f"{ROOT}/items/{item.id}/check", json={"values": {"diameter": 36}})
    assert rejected.json() == {"valid": False, "violations": ["Ограничение печи"]}
    variant = client.post(f"{ROOT}/items/{item.id}/variants", json={
        "number": "PZ-CONF-30", "name": "Пицца 30 см", "values": {"diameter": 30}})
    assert variant.status_code == 201, variant.text
    variant_id = variant.json()["item"]["id"]
    assert variant.json()["configuration"]["template_id"] == item.id
    assert variant.json()["values"] == {"diameter": 30}
    order = client.post(f"{ROOT}/orders", json={"number": "ORDER-7", "customer": "Иван",
                                               "order_date": str(date.today())}).json()
    order_id = order["id"]
    assert client.post(f"{ROOT}/orders/{order_id}/agree").status_code == 400
    endpoint = f"{ROOT}/orders/{order_id}/positions"
    assert client.post(endpoint, json={"number": 1, "item_id": item.id, "quantity": 2}).status_code == 400
    position = client.post(endpoint, json={"number": 1, "item_id": variant_id, "quantity": 2})
    assert position.status_code == 201, position.text
    position_id = position.json()["id"]
    assert client.put(f"{endpoint}/{position_id}", json={"number": 1, "item_id": variant_id,
                                                       "quantity": 3}).status_code == 200
    document = client.get(f"{ROOT}/orders/{order_id}").json()
    assert document["positions"][0]["values"]["diameter"] == 30
    assert Decimal(str(document["positions"][0]["quantity"])) == Decimal(3)
    assert client.post(f"{ROOT}/orders/{order_id}/agree").json()["status"] == "agreed"
    assert client.delete(f"{endpoint}/{position_id}").status_code == 409


@pytest.mark.parametrize("values", [{}, {"diameter": 0}, {"diameter": 41}, {"diameter": True},
                                      {"diameter": "30"}, {"diameter": 30, "unknown": 1}])
def test_bad_variant_is_not_partially_saved(client, session, configurator, values):
    response = client.post(f"{ROOT}/items/{configurator.id}/variants", json={
        "number": "BAD-VARIANT", "name": "Ошибочный вариант", "values": values})
    assert response.status_code == 400, response.text
    assert session.exec(select(Item).where(Item.number == "BAD-VARIANT")).first() is None


def test_rejected_constraint_does_not_create_variant(client, session, configurator):
    endpoint = f"{ROOT}/items/{configurator.id}"
    assert client.post(endpoint + "/constraints", json={"name": "Запрет", "expression": const(False)}).status_code == 201
    response = client.post(endpoint + "/variants", json={"number": "NO", "name": "Нет", "values": {"diameter": 30}})
    assert response.status_code == 400
    assert session.exec(select(VariantParameterValue)).all() == []


def test_order_position_database_constraints(session, configurator):
    from sqlalchemy.exc import IntegrityError
    from src.models.configuration import CustomerOrder
    order = CustomerOrder(number="DB-7", customer="Иван", order_date=date.today())
    session.add(order)
    session.flush()
    with pytest.raises(IntegrityError), session.begin_nested():
        session.add(CustomerOrderPosition(order_id=order.id, number=1, item_id=configurator.id, quantity=0))
        session.flush()
