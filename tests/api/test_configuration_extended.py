from decimal import Decimal

from tests.e2e.test_lab7_scenarios import configurator  # noqa: F401
from tests.unit.test_constraint_interpreter import const, op, param

ROOT = "/api/configuration"


def test_invalid_function_and_rule_are_rejected_before_save(client, configurator):
    assert client.post(ROOT + "/functions", json={"code": "bad", "name": "Ошибка",
        "definition": {"parameters": {}, "result": "bool", "body": const(1)}}).status_code == 400
    assert client.post(f"{ROOT}/items/{configurator.id}/constraints", json={
        "name": "Ошибка", "expression": op("ge", param("unknown"), const(1))}).status_code == 400
    assert client.post(f"{ROOT}/items/{configurator.id}/constraints", json={
        "name": "Не логическое", "expression": const(1)}).status_code == 400


def test_edit_parameters_before_variants_and_freeze_after(client, configurator):
    item = configurator
    spec = client.get(f"{ROOT}/items/{item.id}/parameters").json()[0]
    endpoint = f"{ROOT}/classes/{item.item_class_id}/parameters/{spec['parameter_id']}"
    data = {"parameter_id": spec["parameter_id"], "min_value": 25, "max_value": 35}
    assert client.put(endpoint, json=data).status_code == 200
    response = client.post(f"{ROOT}/items/{item.id}/variants", json={
        "name": "Вариант", "number": "V1", "values": {"diameter": 30}})
    assert response.status_code == 201
    assert client.put(endpoint, json=data).status_code == 409
    assert client.delete(endpoint).status_code == 409


def test_order_edit_print_escaping_delete_and_missing_technology(client, configurator):
    item = configurator
    variant = client.post(f"{ROOT}/items/{item.id}/variants", json={
        "name": "<script>test</script>", "number": "SAFE", "values": {"diameter": 30}}).json()["item"]
    data = {"number": "PRINT", "customer": "<b>Иван</b>", "order_date": "2026-11-15"}
    order = client.post(ROOT + "/orders", json=data).json()
    endpoint = f"{ROOT}/orders/{order['id']}"
    assert client.put(endpoint, json=dict(data, number="PRINT-2")).status_code == 200
    position = client.post(endpoint + "/positions", json={"number": 1, "item_id": variant["id"], "quantity": 2})
    assert position.status_code == 201
    page = client.get(endpoint + "/print")
    assert "text/html" in page.headers["content-type"]
    assert "&lt;script&gt;test&lt;/script&gt;" in page.text
    assert "<script>test</script>" not in page.text
    assert client.get(endpoint + "/cost?pricelist_set_id=1").status_code == 409
    assert client.delete(endpoint).status_code == 204
    assert client.get(endpoint).status_code == 404
