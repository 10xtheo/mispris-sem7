from sqlmodel import select

from src.models import ItemClassifier, EnumType, EnumValue, Parameter
from tests.e2e.test_lab7_scenarios import configurator  # noqa: F401

ROOT = "/api/configuration"


def test_parameter_inheritance_nearest_override_flag_and_restoration(client, session, configurator):
    item = configurator
    inherited = client.get(f"{ROOT}/items/{item.id}/parameters").json()[0]
    child = ItemClassifier(name="Подкласс", parent_id=item.item_class_id)
    session.add(child)
    session.flush()
    item.item_class_id = child.id
    session.add(item)
    session.flush()
    url = f"{ROOT}/classes/{child.id}/parameters"
    assert client.get(f"{ROOT}/items/{item.id}/parameters").json()[0]["min_value"] == 20
    data = {"parameter_id": inherited["parameter_id"], "flag_conf": False}
    assert client.post(url, json=data).status_code == 201
    assert client.get(f"{ROOT}/items/{item.id}/parameters").json() == []
    data.update(flag_conf=True, min_value=28, max_value=32)
    endpoint = url + f"/{inherited['parameter_id']}"
    assert client.put(endpoint, json=data).status_code == 200
    assert client.get(f"{ROOT}/items/{item.id}/parameters").json()[0]["min_value"] == 28
    assert client.delete(endpoint).status_code == 204
    assert client.get(f"{ROOT}/items/{item.id}/parameters").json()[0]["min_value"] == 20


def test_optional_enum_membership_and_human_readable_value(client, session, configurator):
    param_type = session.exec(select(EnumType).where(EnumType.code == "param_type")).one()
    typ = EnumValue(enum_type_id=param_type.id, order_number=2, name="Перечисление", code="enum")
    choices = EnumType(name="Добавки", code="topping-test")
    session.add(typ); session.add(choices); session.flush()
    value = EnumValue(enum_type_id=choices.id, name="Базилик", code="basil", order_number=1)
    session.add(value); session.flush()
    parameter = Parameter(code="topping", name="Добавка", param_type_id=typ.id, enum_type_id=choices.id)
    session.add(parameter); session.flush()
    assert client.post(f"{ROOT}/classes/{configurator.item_class_id}/parameters", json={
        "parameter_id": parameter.id, "required": False}).status_code == 201
    endpoint = f"{ROOT}/items/{configurator.id}/variants"
    assert client.post(endpoint, json={"number": "E-BAD", "name": "Ошибка", "values": {
        "diameter": 30, "topping": typ.id}}).status_code == 400
    result = client.post(endpoint, json={"number": "E-OK", "name": "Вариант", "values": {
        "diameter": 30, "topping": value.id}})
    assert result.status_code == 201
    assert next(row for row in result.json()["parameter_details"] if row["code"] == "topping")["value"] == "Базилик"
