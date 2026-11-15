from src.models import Pricelist, PricelistSet
from tests.helpers import Catalog


def test_order_cost_has_independent_purchase_oracle(client, session):
    catalog = Catalog(session)
    product = catalog.item("Покупное блюдо", "assembly", base_unit="шт")
    operation = client.post(f"/api/items/{product.id}/technology/operations", json={
        "number": 10, "name": "Закупка", "kind": "purchase", "is_output": True})
    assert operation.status_code == 201
    price_set = PricelistSet()
    session.add(price_set)
    session.flush()
    session.add(Pricelist(pricelist_set_id=price_set.id, item_id=product.id, price="12.50"))
    session.flush()
    order = client.post("/api/configuration/orders", json={"number": "COST", "customer": "Иван",
                                                          "order_date": "2026-11-15"}).json()
    assert client.post(f"/api/configuration/orders/{order['id']}/positions", json={
        "number": 1, "item_id": product.id, "quantity": 3}).status_code == 201
    result = client.get(f"/api/configuration/orders/{order['id']}/cost?pricelist_set_id={price_set.id}")
    assert result.status_code == 200, result.text
    assert result.json()["total_cost"] == 37.5  # 3 × 12,50, труд отсутствует
