from tests.unit.test_constraint_interpreter import const, op


def test_evaluate_and_invalid_expression(client):
    response = client.post("/api/configuration/evaluate", json={"expression": op("/", const(3), const(2))})
    assert response.status_code == 200
    assert response.json()["result"] == 1.5
    assert client.post("/api/configuration/evaluate", json={"expression": {
        "kind": "param", "name": []}}).status_code == 400
    assert client.post("/api/configuration/evaluate", json={"expression": op("/", const(3), const(0))}).status_code == 400


def test_missing_order_and_input_validation(client):
    assert client.get("/api/configuration/orders/999999").status_code == 404
    assert client.post("/api/configuration/orders", json={"number": "", "customer": "X",
                                                         "order_date": "2026-11-15"}).status_code == 422


def test_openapi_configuration_has_russian_summaries(client):
    schema = client.get("/openapi.json").json()
    routes = [entry for path, methods in schema["paths"].items() if path.startswith("/api/configuration")
              for entry in methods.values() if isinstance(entry, dict)]
    assert len(routes) >= 18
    assert all(any("а" <= char.lower() <= "я" for char in entry["summary"]) for entry in routes)


def test_dedicated_swagger_is_subset_of_actual_api(client):
    schema = client.get("/openapi-lab7.json").json()
    assert len(schema["paths"]) >= 18
    assert all(path.startswith("/api/configuration") for path in schema["paths"])
    assert "/openapi-lab7.json" in client.get("/docs/lab7").text
