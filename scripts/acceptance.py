"""Приёмочные испытания задания №5 на работающем сервере (как при показе через Swagger).

1) перезагружает демо-данные (python data/seed.py);
2) проходит требования Ф1–Ф6 запросами к API и сверяет результаты;
3) снова перезагружает демо-данные, чтобы оставить БД в исходном состоянии для показа.

Запуск (сервер должен работать):
    uvicorn src.main:app --port 8000 &
    python scripts/acceptance.py [http://localhost:8000]
"""

import os
import sys
import time
from decimal import Decimal

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.seed import main as reseed  # noqa: E402

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")
api = httpx.Client(base_url=BASE, timeout=30)
results: list[tuple[str, str, bool, str]] = []


def check(req: str, title: str, ok: bool, detail: str = "") -> None:
    results.append((req, title, ok, detail))
    print(f"{'✔' if ok else '✘'} [{req}] {title}" + (f" — {detail}" if detail else ""))


def get(path, **params):
    r = api.get(path, params=params)
    r.raise_for_status()
    return r.json()


def items_by_number():
    return {i["number"]: i for i in get("/api/items/", limit=1000)}


def norms(item_id, qty, class_id=None):
    params = {"quantity": qty}
    if class_id:
        params["class_id"] = class_id
    return {r["component_name"]: Decimal(r["total_quantity"]) for r in get(f"/api/items/{item_id}/bom/norms", **params)["rows"]}


def spec(item_id, at=None):
    params = {"at": at} if at else {}
    return {r["component_name"]: r for r in get(f"/api/items/{item_id}/bom", **params)["rows"]}


def main() -> None:
    reseed()
    print(f"Сервер: {BASE}\n")

    # ---- 0. Сервер
    check("О7", "Сервер отвечает, Swagger доступен",
          api.get("/health").json() == {"status": "ok"} and api.get("/docs").status_code == 200)
    paths = get("/openapi.json")["paths"]
    need = ["/api/items/{item_id}/bom", "/api/items/{item_id}/bom/tree", "/api/items/{item_id}/bom/norms",
            "/api/items/{item_id}/bom/changes", "/api/items/{item_id}/modifications",
            "/api/items/{item_id}/bom/{component_id}", "/api/items/{item_id}/bom/{component_id}/replace"]
    check("О7", "Все эндпоинты №5 опубликованы в OpenAPI", all(p in paths for p in need))

    it = items_by_number()
    pizza, combo, mod, flour = it["PZ-001"], it["CB-001"], it["PZ-001-01"], it["RM-001"]
    moz, dough, basil, jal, parm = it["RM-010"], it["SF-001"], it["RM-030"], it["RM-021"], it["RM-011"]
    classes = {c["name"]: c["id"] for c in get("/api/classifiers/items", limit=1000)}
    types = {t["code"]: t["id"] for t in get("/api/enums/types")}
    type_codes = {v["id"]: v["code"] for v in get(f"/api/enums/values/by-type/{types['item_type']}")}

    # ---- Ф1. Справочник изделий с типами
    kinds = {type_codes[i["item_type_id"]] for i in it.values()}
    check("Ф1", "В справочнике есть все 4 типа изделий", kinds == {"material", "detail", "assembly", "complex"},
          ", ".join(sorted(kinds)))
    check("Ф1.4", "Изделия привязаны к классам иерархического классификатора",
          all(i["item_class_id"] for i in it.values()) and len(classes) >= 10, f"{len(classes)} классов")
    r = api.post(f"/api/items/{flour['id']}/bom", json={"component_item_id": it["RM-020"]["id"], "quantity": "1"})
    check("Ф1/Ф2.3", "У материала нельзя создать состав (400)", r.status_code == 400, r.json()["detail"])
    r = api.post("/api/items/", json={"number": "PZ-001", "name": "Дубль"})
    check("Ф1.1", "Обозначение изделия уникально (409)", r.status_code == 409)

    # ---- Ф2. Спецификация с нормами
    s = spec(pizza["id"])
    check("Ф2", "Спецификация пиццы: 5 позиций в заданном порядке",
          list(s) == ["Тесто для пиццы", "Соус томатный", "Моцарелла", "Базилик свежий", "Коробка для пиццы 30 см"])
    check("Ф2.1/2.2", "Норма в граммах: моцарелла 130 г (после правки в демо-данных)",
          s["Моцарелла"]["quantity"] == "130.000000" and s["Моцарелла"]["unit_symbol"] == "г")
    d = spec(dough["id"])
    check("Ф2.1", "«Для количества»: нормы теста даны на 10 кг замеса",
          d["Мука пшеничная в/с"]["for_quantity"] == "10.000000")
    check("Ф2.1", "Флаг базы: коробка — только у базового изделия (is_base=false)",
          s["Коробка для пиццы 30 см"]["is_base"] is False)
    new = api.post("/api/items/", json={"number": "ACC-1", "name": "Орегано сушёный",
                                        "item_type_id": next(k for k, v in type_codes.items() if v == "material"),
                                        "item_class_id": classes["Специи и зелень"]}).json()
    api.post("/api/items/units", json={"item_id": new["id"], "unit_simple_id": get("/api/units/")[0]["id"], "is_base": True})
    r = api.post(f"/api/items/{pizza['id']}/bom", json={"component_item_id": new["id"], "quantity": "0.002", "order_number": 6,
                                                       "reason": "Новый рецепт"})
    check("Ф2", "Добавление компонента в состав (201)", r.status_code == 201)
    r = api.post(f"/api/items/{pizza['id']}/bom", json={"component_item_id": new["id"], "quantity": "1"})
    check("Ф2", "Повторное добавление того же компонента запрещено (409)", r.status_code == 409)
    r = api.post(f"/api/items/{pizza['id']}/bom", json={"component_item_id": moz["id"], "quantity": "0"})
    check("Ф2.1", "Нулевая норма отклоняется валидацией (422)", r.status_code == 422)

    # ---- Ф5. Состав на всю глубину
    tree = get(f"/api/items/{combo['id']}/bom/tree")["nodes"]
    lv = {(n["component_name"], n["lvl"]) for n in tree}
    check("Ф5", "FIND_BOM набора: 3 уровня вложенности",
          max(n["lvl"] for n in tree) == 3 and ("Мука пшеничная в/с", 3) in lv and ("Тесто для пиццы", 2) in lv,
          f"{len(tree)} узлов")
    flour_node = next(n for n in tree if n["component_name"] == "Мука пшеничная в/с")
    check("Ф5", "Норма муки на 1 набор = 2 × 0.25 × 6/10 = 0.3 кг", flour_node["norm"] == "0.300000")
    r = api.post(f"/api/items/{dough['id']}/bom", json={"component_item_id": combo["id"], "quantity": "1"})
    check("Ф2.3/Ф5", "Цикл в составе запрещён (400)", r.status_code == 400 and "цикл" in r.json()["detail"])
    check("Ф5", "После отклонённой операции состав не изменился (откат транзакции)",
          "Комбо «Обед на двоих»" not in spec(dough["id"]))

    # ---- Ф6. Сводные нормы
    n10 = norms(combo["id"], 10)
    expect = {"Мука пшеничная в/с": "3", "Вода питьевая": "1.8", "Моцарелла": "2.6", "Пармезан": "0.21",
              "Томаты": "1.92", "Базилик свежий": "0.116", "Коробка для пиццы 30 см": "20"}
    bad = {k: str(n10.get(k)) for k, v in expect.items() if n10.get(k) != Decimal(v)}
    check("Ф6", "CALC_BOM на 10 наборов: контрольные значения совпадают", not bad, str(bad) if bad else "7 из 7")
    cheese = norms(combo["id"], 10, classes["Молочные продукты"])
    check("Ф6/Ф1.4", "Нормы по классу «Молочные продукты» (включая подкласс «Сыры»)",
          set(cheese) == {"Моцарелла", "Пармезан"})
    semi = norms(combo["id"], 10, classes["Полуфабрикаты"])
    check("Ф6", "Нормы по классу «Полуфабрикаты» без двойного счёта сырья",
          semi.get("Тесто для пиццы") == Decimal("5") and "Мука пшеничная в/с" not in semi)
    rows = get(f"/api/items/{combo['id']}/bom/norms", quantity=10)["rows"]
    check("Ф6.1", "Нормы агрегированы по классам ресурсов (у строк есть класс, сортировка по классу)",
          all(r_["class_name"] for r_ in rows) and [r_["class_name"] for r_ in rows] == sorted(r_["class_name"] for r_ in rows))

    # ---- Ф3. Управление изменениями
    before = get(f"/api/items/{pizza['id']}/bom")["at"]
    time.sleep(0.05)
    r = api.put(f"/api/items/{pizza['id']}/bom/{moz['id']}", json={"quantity": "140", "reason": "Акция «Больше сыра»"})
    check("Ф3", "Изменение нормы расхода (200)", r.status_code == 200 and r.json()["quantity"] == "140.000000")
    h = get(f"/api/items/{pizza['id']}/bom/changes")[-1]
    check("Ф3.1", "История: тип, дата, причина, было → стало",
          h["change_type"] == "change_quantity" and h["reason"] == "Акция «Больше сыра»"
          and h["old"]["quantity"] == "130.000000" and h["new"]["quantity"] == "140.000000")
    check("Ф3.1", "Состав на прошлую дату показывает старую норму (130 г)",
          spec(pizza["id"], before)["Моцарелла"]["quantity"] == "130.000000")
    hist_types = [x["change_type"] for x in get(f"/api/items/{pizza['id']}/bom/changes")]
    check("Ф3.2", "REGISTER_CHANGE вызывается при каждой правке", hist_types.count("add_component") == 6
          and "change_quantity" in hist_types, f"{len(hist_types)} записей")

    # ---- Ф4. Модификации
    ms = spec(mod["id"])
    check("Ф4.1", "Модификация PZ-001-01: тесто и соус унаследованы, моцарелла переопределена",
          ms["Тесто для пиццы"]["inherited"] and ms["Соус томатный"]["inherited"]
          and not ms["Моцарелла"]["inherited"] and ms["Моцарелла"]["quantity"] == "150.000000")
    check("Ф4.1", "В модификации добавлен халапеньо и удалён базилик",
          "Халапеньо" in ms and "Базилик свежий" not in ms)
    check("Ф4.1", "Новый компонент базы (орегано) виден в модификации, коробка (не база) — своя",
          "Орегано сушёный" in ms and not ms["Коробка для пиццы 30 см"]["inherited"])
    mn = norms(mod["id"], 10)
    # на 10 пицц: моцарелла 150 г, халапеньо 30 г (свои строки); базилик только из соуса
    # 10 г/кг × 0.08 кг = 0.8 г (прямой базилик исключён); мука из унаследованного теста 0.25 × 0.6
    want = {"Моцарелла": "1.5", "Халапеньо": "0.3", "Базилик свежий": "0.008", "Мука пшеничная в/с": "1.5"}
    got = {k: str(mn.get(k)) for k in want}
    check("Ф6.2", "Нормы модификации на 10 шт = своя + базовая спецификация",
          all(mn.get(k) == Decimal(v) for k, v in want.items()), str(got))
    api.put(f"/api/items/{pizza['id']}/bom/{dough['id']}", json={"quantity": "0.3", "reason": "Бортик толще"})
    check("Ф4.1", "Изменение базы (тесто 0.3) автоматически действует в модификации",
          spec(mod["id"])["Тесто для пиццы"]["quantity"] == "0.300000")
    r = api.post(f"/api/items/{pizza['id']}/modifications", json={"name": "Маргарита без лактозы", "reason": "Диетическое меню"})
    m2 = r.json()
    check("Ф4", "CREATE_MODIFICATION: новая модификация с обозначением PZ-001-02",
          r.status_code == 201 and m2["number"] == "PZ-001-02" and m2["base_item_id"] == pizza["id"])
    r = api.post(f"/api/items/{m2['id']}/bom/{moz['id']}/replace",
                 json={"new_component_item_id": parm["id"], "quantity": "60",
                       "unit_quantity_id": next(u["id"] for u in get(f"/api/items/{parm['id']}/units") if not u["is_base"]),
                       "reason": "Безлактозный сыр"})
    check("Ф4.1", "Замена компонента в модификации (моцарелла → пармезан)", r.status_code == 200)
    m2s = spec(m2["id"])
    check("Ф4.1", "База при этом не изменилась", "Моцарелла" in spec(pizza["id"]) and "Моцарелла" not in m2s
          and "Пармезан" in m2s)
    check("Ф3", "История модификации: создание и замена",
          [x["change_type"] for x in get(f"/api/items/{m2['id']}/bom/changes")] == ["create_modification", "replace_component"])
    r = api.delete(f"/api/items/{pizza['id']}")
    check("Ф4", "Нельзя удалить базовое изделие, у которого есть модификации и применение (409)", r.status_code == 409)

    # ---- Итог
    reseed()
    ok = sum(1 for x in results if x[2])
    print(f"\nИтого: {ok} из {len(results)} проверок пройдено. Демо-данные восстановлены.")
    sys.exit(0 if ok == len(results) else 1)


if __name__ == "__main__":
    main()
