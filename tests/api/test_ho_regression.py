"""Регрессия задания №4 (ХО) после рефакторинга транзакций и исключений."""


def ok(r, status=200):
    assert r.status_code == status, (r.status_code, r.text)
    return r.json() if r.content else None


def setup_ho_type(client):
    pt = ok(client.post("/api/enums/types", json={"code": "param_type", "name": "Тип параметра"}), 201)
    number = ok(client.post("/api/enums/values", json={
        "enum_type_id": pt["id"], "order_number": 1, "code": "number", "name": "Числовой"}), 201)
    p_amount = ok(client.post("/api/parameters/", json={
        "code": "order_sum", "name": "Сумма заказа", "param_type_id": number["id"]}), 201)
    ho_type = ok(client.post("/api/classifiers/ho", json={"name": "Доставка заказа", "code": "delivery"}), 201)
    cp = ok(client.post("/api/ho/class-parameters", json={
        "ho_type_id": ho_type["id"], "parameter_id": p_amount["id"], "min_value": "0", "max_value": "100000"}), 201)
    return ho_type, cp


def test_ins_ho_creates_parameter_placeholders(client):
    ho_type, cp = setup_ho_type(client)
    ho = ok(client.post("/api/ho/", json={"ho_type_id": ho_type["id"], "op_date": "2026-10-11"}), 201)
    params = ok(client.get(f"/api/ho/{ho['id']}/parameters"))
    assert [p["ho_class_param_id"] for p in params] == [cp["id"]]
    assert params[0]["value_real"] is None and params[0]["parameter_code"] == "order_sum"


def test_write_ho_par_checks_range(client):
    ho_type, cp = setup_ho_type(client)
    ho = ok(client.post("/api/ho/", json={"ho_type_id": ho_type["id"], "op_date": "2026-10-11"}), 201)
    r = client.put(f"/api/ho/{ho['id']}/parameters/{cp['id']}", json={"value_real": "250000"})
    assert r.status_code == 400
    r = client.put(f"/api/ho/{ho['id']}/parameters/{cp['id']}", json={"value_real": "1500.50"})
    assert r.status_code == 200
    full = ok(client.get(f"/api/ho/{ho['id']}/full"))
    assert full["parameters"][0]["value_real"] == "1500.500000"


def test_set_ho_actor_requires_available_role(client):
    ho_type, _ = setup_ho_type(client)
    ho = ok(client.post("/api/ho/", json={"ho_type_id": ho_type["id"], "op_date": "2026-10-11"}), 201)
    role = ok(client.post("/api/roles/", json={"name": "Курьер"}), 201)
    st = ok(client.post("/api/enums/types", json={"code": "sxd_type", "name": "Тип СХД"}), 201)
    legal = ok(client.post("/api/enums/values", json={
        "enum_type_id": st["id"], "order_number": 1, "code": "legal", "name": "ЮЛ"}), 201)
    sxd = ok(client.post("/api/sxd/", json={"name": "ООО Быстрая доставка", "entity_type_id": legal["id"]}), 201)
    r = client.post(f"/api/ho/{ho['id']}/roles", json={"sxd_id": sxd["id"], "role_id": role["id"]})
    assert r.status_code == 400  # роль не разрешена для типа ХО
    ok(client.post("/api/roles/available", json={"ho_type_id": ho_type["id"], "role_id": role["id"], "max_count": 1}), 201)
    ok(client.post(f"/api/ho/{ho['id']}/roles", json={"sxd_id": sxd["id"], "role_id": role["id"]}), 201)
    r = client.post(f"/api/ho/{ho['id']}/roles", json={"sxd_id": sxd["id"], "role_id": role["id"]})
    assert r.status_code == 400  # превышен max_count


def test_not_found_is_404(client):
    assert client.get("/api/ho/999999").status_code == 404
    assert client.get("/api/ho/999999/full").status_code == 404
