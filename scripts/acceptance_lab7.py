"""Приёмочные HTTP-испытания №7 на отдельном стенде localhost:8007."""
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE = "http://localhost:8007"
OUT = Path(os.environ.get("LAB7_PROTOCOL_DIR", Path(__file__).resolve().parents[1] / "utils/lab7/protocols"))
results = []


def request(method, path, body=None, status=200):
    req = Request(BASE + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                  headers={"Content-Type": "application/json"})
    try:
        with urlopen(req) as response:
            code, text = response.status, response.read().decode()
    except HTTPError as exc:
        code, text = exc.code, exc.read().decode()
    assert code == status, (path, code, text)
    value = json.loads(text) if text and not text.startswith("<!doctype") else text
    results.append({"method": method, "path": path, "expected_status": status,
                    "actual_status": code, "request": body, "response": value})
    return value


def main():
    request("GET", "/health")
    items = request("GET", "/api/items/?limit=100")
    template = next(item["id"] for item in items if item["number"] == "PZ-CONF")
    variant = next(item["id"] for item in items if item["number"] == "PZ-CONF-30")
    prefix = f"/api/configuration/items/{template}"
    types = request("GET", "/api/enums/types")
    enum_id = next(row["id"] for row in types if row["code"] == "pizza_topping")
    topping = next(row["id"] for row in request("GET", f"/api/enums/values/by-type/{enum_id}") if row["code"] == "basil")
    params = request("GET", prefix + "/parameters")
    assert {p["code"] for p in params} == {"diameter", "cheese_g", "topping"}
    assert len(request("GET", prefix + "/constraints")) == 2
    assert request("POST", prefix + "/check", {"values": {"diameter": 30, "cheese_g": 130, "topping": topping}})["valid"]
    bad = {"diameter": 35, "cheese_g": 100, "topping": topping}
    assert not request("POST", prefix + "/check", {"values": bad})["valid"]
    request("POST", prefix + "/variants", {"number": "BAD-ACC", "name": "Ошибочный вариант", "values": bad}, 400)
    assert not any(item["number"] == "BAD-ACC" for item in request("GET", "/api/items/?limit=100"))
    request("POST", prefix + "/check", {"values": {"diameter": 30, "cheese_g": 130, "topping": 999999}}, 404)
    request("POST", "/api/configuration/evaluate", {"expression": {"kind": "op", "op": "/", "args": [
        {"kind": "const", "value": 1}, {"kind": "const", "value": 0}]}}, 400)
    doc = request("GET", "/api/configuration/orders/1")
    assert len(doc["positions"]) == 2
    assert doc["positions"][0]["parameter_details"][2]["value"] == "Базилик"
    cost = request("GET", "/api/configuration/orders/1/cost?pricelist_set_id=1")
    assert str(cost["total_cost"]) == "628.25"
    page = request("GET", "/api/configuration/orders/1/print")
    assert "ORDER-007" in page and "Базилик" in page and "см" in page
    order = request("POST", "/api/configuration/orders", {"number": "ACC-7", "customer": "Испытатель",
        "order_date": "2026-11-15"}, 201)
    url = f"/api/configuration/orders/{order['id']}"
    request("POST", url + "/positions", {"number": 1, "item_id": template, "quantity": 1}, 400)
    position = request("POST", url + "/positions", {"number": 1, "item_id": variant, "quantity": 1}, 201)
    request("PUT", url + f"/positions/{position['id']}", {"number": 1, "item_id": variant, "quantity": 2})
    request("POST", url + "/agree")
    request("DELETE", url + f"/positions/{position['id']}", status=409)
    OUT.mkdir(exist_ok=True, parents=True)
    (OUT / "acceptance_protocol.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "acceptance_protocol.txt").write_text(f"HTTP acceptance: {len(results)} checks passed\n"
        + "\n".join(f"{r['actual_status']} {r['method']} {r['path']}" for r in results), encoding="utf-8")
    print(f"HTTP acceptance: {len(results)} checks passed")


if __name__ == "__main__":
    main()
