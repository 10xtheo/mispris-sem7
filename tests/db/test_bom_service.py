"""Уровень 2 — сервис BOM на реальной БД: изменения, версии, модификации, история, ошибки."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlmodel import Session

from src.core.errors import BusinessRuleError, ConflictError, NotFoundError
from src.schemas.bom import BomComponentAdd, BomComponentReplace, BomComponentUpdate, ModificationCreate
from tests.helpers import build_food_catalog

D = Decimal


@pytest.fixture()
def cat(session: Session):
    return build_food_catalog(session)


def spec(cat, key, at=None):
    return {r.component_name: r for r in cat.service.get_spec(cat.id(key), at).rows}


def norms(cat, key, qty="1", class_name=None):
    class_id = cat.classes[class_name].id if class_name else None
    res = cat.service.calc_bom(cat.id(key), D(qty), class_id)
    return {r.component_name: r.total_quantity for r in res.rows}


# ------------------------------------------------------------ редактирование спецификации
def test_add_component_registers_change(cat):
    cat.item("Орегано", "material", "Специи и зелень", extra_units={"г": "0.001"})
    row = cat.add("Пицца Маргарита", "Орегано", "2", unit="г", order=5)
    assert row.component_name == "Орегано" and row.quantity == D("2") and row.unit_symbol == "г"
    history = cat.service.history(cat.id("Пицца Маргарита"))
    last = history[-1]
    assert last.change_type == "add_component"
    assert last.old is None and last.new.component_name == "Орегано"


def test_default_unit_is_component_base_unit(cat):
    cat.item("Соль", "material", "Специи и зелень")
    row = cat.add("Тесто для пиццы", "Соль", "0.01")
    assert row.unit_symbol == "кг"


def test_change_quantity_creates_new_version_and_diff(cat):
    t0 = datetime.now(timezone.utc)
    cat.service.update_component(
        cat.id("Пицца Маргарита"), cat.id("Моцарелла"),
        BomComponentUpdate(quantity=D("150"), reason="Больше сыра по отзывам клиентов"),
    )
    assert spec(cat, "Пицца Маргарита")["Моцарелла"].quantity == D("150")
    assert spec(cat, "Пицца Маргарита", t0)["Моцарелла"].quantity == D("120")  # состав на прошлую дату
    change = cat.service.history(cat.id("Пицца Маргарита"))[-1]
    assert change.change_type == "change_quantity"
    assert change.reason == "Больше сыра по отзывам клиентов"
    assert (change.old.quantity, change.new.quantity) == (D("120"), D("150"))
    assert change.old.valid_to == change.new.valid_from  # версии стыкуются без разрыва


def test_remove_component(cat):
    cat.service.remove_component(cat.id("Пицца Маргарита"), cat.id("Базилик"), "Убрали свежий базилик")
    assert "Базилик" not in spec(cat, "Пицца Маргарита")
    assert norms(cat, "Пицца Маргарита")["Базилик"] == pytest.approx(D("0.0008"))  # остался базилик в соусе
    change = cat.service.history(cat.id("Пицца Маргарита"))[-1]
    assert change.change_type == "remove_component" and change.new is None


def test_replace_component(cat):
    cat.item("Сулугуни", "material", "Сыры", extra_units={"г": "0.001"})
    row = cat.service.replace_component(
        cat.id("Пицца Маргарита"), cat.id("Моцарелла"),
        BomComponentReplace(
            new_component_item_id=cat.id("Сулугуни"), quantity=D("110"),
            unit_quantity_id=cat.uq[("Сулугуни", "г")].id, reason="Замена поставщика",
        ),
    )
    assert row.component_name == "Сулугуни" and row.order_number == 3
    names = list(spec(cat, "Пицца Маргарита"))
    assert "Моцарелла" not in names and "Сулугуни" in names
    change = cat.service.history(cat.id("Пицца Маргарита"))[-1]
    assert change.change_type == "replace_component"
    assert (change.old.component_name, change.new.component_name) == ("Моцарелла", "Сулугуни")


def test_readd_after_remove(cat):
    pizza, basil = cat.id("Пицца Маргарита"), cat.id("Базилик")
    cat.service.remove_component(pizza, basil)
    row = cat.add("Пицца Маргарита", "Базилик", "7", unit="г")
    assert row.quantity == D("7")


# ------------------------------------------------------------ ошибки и правила
def test_duplicate_component_conflict(cat):
    with pytest.raises(ConflictError):
        cat.add("Пицца Маргарита", "Моцарелла", "1", unit="г")


def test_material_cannot_have_spec(cat):
    with pytest.raises(BusinessRuleError):
        cat.add("Мука пшеничная", "Вода питьевая", "1")


def test_cycle_is_rejected(cat):
    with pytest.raises(BusinessRuleError, match="цикл"):
        cat.add("Тесто для пиццы", "Комбо на двоих", "1")


def test_unit_of_other_item_is_rejected(cat):
    with pytest.raises(BusinessRuleError, match="другому изделию"):
        cat.service.add_component(
            cat.id("Тесто для пиццы"),
            BomComponentAdd(
                component_item_id=cat.id("Мука пшеничная"), quantity=D("1"),
                unit_quantity_id=cat.uq[("Моцарелла", "г")].id,
            ),
        )


def test_update_missing_component_not_found(cat):
    with pytest.raises(NotFoundError):
        cat.service.update_component(
            cat.id("Пицца Маргарита"), cat.id("Пармезан"), BomComponentUpdate(quantity=D("1"))
        )


def test_remove_missing_component_not_found(cat):
    with pytest.raises(NotFoundError):
        cat.service.remove_component(cat.id("Пицца Маргарита"), cat.id("Пармезан"))


def test_replace_with_already_present_conflict(cat):
    with pytest.raises(ConflictError):
        cat.service.replace_component(
            cat.id("Пицца Маргарита"), cat.id("Моцарелла"),
            BomComponentReplace(new_component_item_id=cat.id("Базилик"), quantity=D("1")),
        )


def test_calc_bom_validation(cat):
    with pytest.raises(BusinessRuleError):
        cat.service.calc_bom(cat.id("Пицца Маргарита"), D("0"))
    with pytest.raises(NotFoundError):
        cat.service.calc_bom(cat.id("Пицца Маргарита"), D("1"), class_id=999999)


# ------------------------------------------------------------ модификации
@pytest.fixture()
def spicy(cat):
    """«Маргарита острая»: моцарелла 150 г, + халапеньо 30 г, − свежий базилик."""
    mod = cat.service.create_modification(
        cat.id("Пицца Маргарита"), ModificationCreate(name="Пицца Маргарита острая")
    )
    cat.items["Маргарита острая"] = mod
    mod_id = mod.id
    cat.service.update_component(mod_id, cat.id("Моцарелла"), BomComponentUpdate(quantity=D("150")))
    cat.service.add_component(
        mod_id,
        BomComponentAdd(
            component_item_id=cat.id("Халапеньо"), quantity=D("30"),
            unit_quantity_id=cat.uq[("Халапеньо", "г")].id, order_number=5,
        ),
    )
    cat.service.remove_component(mod_id, cat.id("Базилик"))
    return mod


def test_modification_defaults(cat, spicy):
    base = cat.items["Пицца Маргарита"]
    assert spicy.base_item_id == base.id
    assert spicy.number == f"{base.number}-01"
    assert spicy.item_type_id == base.item_type_id and spicy.item_class_id == base.item_class_id
    assert [m.id for m in cat.service.get_modifications(base.id)] == [spicy.id]
    first = cat.service.history(spicy.id)[0]
    assert first.change_type == "create_modification"


def test_modification_spec_is_base_plus_own_changes(cat, spicy):
    rows = spec(cat, "Маргарита острая")
    assert set(rows) == {"Тесто для пиццы", "Соус томатный", "Моцарелла", "Халапеньо"}
    assert rows["Тесто для пиццы"].inherited is True  # унаследовано от базы
    assert rows["Моцарелла"].inherited is False and rows["Моцарелла"].quantity == D("150")
    # база не изменилась
    base = spec(cat, "Пицца Маргарита")
    assert base["Моцарелла"].quantity == D("120") and "Базилик" in base and "Халапеньо" not in base


def test_modification_norms(cat, spicy):
    n = norms(cat, "Маргарита острая", "10")
    assert n["Моцарелла"] == pytest.approx(D("1.5"))
    assert n["Халапеньо"] == pytest.approx(D("0.3"))
    assert n["Базилик"] == pytest.approx(D("0.008"))  # только из соуса
    assert n["Мука пшеничная"] == pytest.approx(D("1.5"))


def test_base_change_propagates_to_modification(cat, spicy):
    cat.service.update_component(
        cat.id("Пицца Маргарита"), cat.id("Тесто для пиццы"), BomComponentUpdate(quantity=D("0.3"))
    )
    assert spec(cat, "Маргарита острая")["Тесто для пиццы"].quantity == D("0.3")


def test_non_base_row_is_not_inherited(cat, spicy):
    cat.item("Коробка для пиццы", "material", None, base_unit="шт")
    cat.add("Пицца Маргарита", "Коробка для пиццы", "1", is_base=False)
    assert "Коробка для пиццы" in spec(cat, "Пицца Маргарита")
    assert "Коробка для пиццы" not in spec(cat, "Маргарита острая")


def test_modification_cannot_add_inherited_component(cat, spicy):
    with pytest.raises(ConflictError, match="наследуется"):
        cat.service.add_component(
            spicy.id, BomComponentAdd(component_item_id=cat.id("Соус томатный"), quantity=D("1"))
        )


def test_modification_of_modification(cat, spicy):
    extra = cat.service.create_modification(spicy.id, ModificationCreate(name="Острая XL"))
    rows = {r.component_name: r for r in cat.service.get_spec(extra.id).rows}
    assert set(rows) == {"Тесто для пиццы", "Соус томатный", "Моцарелла", "Халапеньо"}
    assert rows["Моцарелла"].quantity == D("150")  # ближайшее переопределение по цепочке
    assert rows["Тесто для пиццы"].inherit_level == 2


def test_cycle_through_modification_is_rejected(cat, spicy):
    # Добавить в соус острую модификацию: острая -> соус -> острая
    with pytest.raises(BusinessRuleError, match="цикл"):
        cat.add("Соус томатный", "Маргарита острая", "1")


def test_duplicate_modification_number_conflict(cat, spicy):
    with pytest.raises(ConflictError):
        cat.service.create_modification(
            cat.id("Пицца Маргарита"), ModificationCreate(name="Ещё", number=spicy.number)
        )
