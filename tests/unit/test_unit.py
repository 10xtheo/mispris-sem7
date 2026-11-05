"""Уровень 1 — модульные тесты без БД: схемы, вспомогательные функции, правила сервиса на заглушках."""

from decimal import Decimal
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.core.errors import BusinessRuleError, ConflictError, DomainError, NotFoundError
from src.schemas.bom import BomComponentAdd, BomComponentReplace, BomComponentUpdate, ModificationCreate
from src.services.bom_service import BomService, next_modification_number, rounded
from src.services.classifier_service import ensure_no_cycle


# ------------------------------------------------------------ доменные ошибки
@pytest.mark.parametrize(
    "exc, status", [(NotFoundError, 404), (BusinessRuleError, 400), (ConflictError, 409)]
)
def test_domain_errors_map_to_http_status(exc, status):
    err = exc("сообщение")
    assert isinstance(err, DomainError)
    assert err.status_code == status
    assert err.detail == "сообщение"


# ------------------------------------------------------------ схемы
def test_add_component_defaults():
    data = BomComponentAdd(component_item_id=1, quantity=Decimal("0.25"))
    assert data.for_quantity == Decimal("1")
    assert data.is_base is True
    assert data.order_number == 0
    assert data.unit_quantity_id is None


@pytest.mark.parametrize("field, value", [("quantity", "0"), ("quantity", "-1"), ("for_quantity", "0")])
def test_add_component_rejects_non_positive(field, value):
    payload = {"component_item_id": 1, "quantity": "1", field: value}
    with pytest.raises(ValidationError):
        BomComponentAdd.model_validate(payload)


def test_add_component_rejects_negative_order():
    with pytest.raises(ValidationError):
        BomComponentAdd.model_validate({"component_item_id": 1, "quantity": "1", "order_number": -1})


def test_update_requires_at_least_one_field():
    with pytest.raises(ValidationError):
        BomComponentUpdate.model_validate({"reason": "только причина"})
    assert BomComponentUpdate.model_validate({"quantity": "2"}).quantity == Decimal("2")


def test_replace_requires_positive_quantity():
    with pytest.raises(ValidationError):
        BomComponentReplace.model_validate({"new_component_item_id": 2, "quantity": "0"})


def test_modification_requires_name():
    with pytest.raises(ValidationError):
        ModificationCreate.model_validate({"name": ""})


# ------------------------------------------------------------ вспомогательные функции
def test_next_modification_number():
    assert next_modification_number("PZ-001", set()) == "PZ-001-01"
    assert next_modification_number("PZ-001", {"PZ-001-01", "PZ-001-02"}) == "PZ-001-03"
    assert next_modification_number("PZ-001", {"PZ-001-02"}) == "PZ-001-01"


def test_rounded_only_selected_decimal_fields():
    row = {"norm": Decimal("0.12345678901"), "quantity": Decimal("0.12345678901"), "name": "x"}
    out = rounded(row, "norm")
    assert out["norm"] == Decimal("0.123457")
    assert out["quantity"] == Decimal("0.12345678901")
    assert out["name"] == "x"


# ------------------------------------------------------------ классификатор без циклов (задание №1)
class FakeClassRepo:
    def __init__(self, parents: dict[int, int | None]):
        self.parents = parents

    def get_by_id(self, obj_id):
        if obj_id not in self.parents:
            return None
        return SimpleNamespace(id=obj_id, parent_id=self.parents[obj_id])


def test_classifier_cycle_detected():
    repo = FakeClassRepo({1: None, 2: 1, 3: 2})  # 1 <- 2 <- 3
    with pytest.raises(BusinessRuleError):
        ensure_no_cycle(repo, 1, 3)  # сделать 1 потомком 3 — цикл
    with pytest.raises(BusinessRuleError):
        ensure_no_cycle(repo, 2, 2)  # сам себе родитель


def test_classifier_move_allowed_and_missing_parent():
    repo = FakeClassRepo({1: None, 2: 1, 3: None})
    ensure_no_cycle(repo, 2, 3)  # перенос ветки — допустимо
    ensure_no_cycle(repo, 2, None)  # в корень — допустимо
    with pytest.raises(NotFoundError):
        ensure_no_cycle(repo, 2, 99)


# ------------------------------------------------------------ правила сервиса на заглушках
class FakeItems:
    def __init__(self, items):
        self.items = {i.id: i for i in items}

    def get_by_id(self, item_id):
        return self.items.get(item_id)


class FakeEnums:
    def get_by_id(self, ev_id):
        return {1: SimpleNamespace(code="material"), 3: SimpleNamespace(code="assembly")}.get(ev_id)


def make_fake_service(items):
    return BomService(
        items=FakeItems(items), boms=None, changes=None, modifications=None,  # type: ignore[arg-type]
        enum_values=FakeEnums(), units=None, classifiers=None, catalog=None,  # type: ignore[arg-type]
    )


def test_material_cannot_have_specification():
    flour = SimpleNamespace(id=1, name="Мука", item_type_id=1)
    salt = SimpleNamespace(id=2, name="Соль", item_type_id=1)
    service = make_fake_service([flour, salt])
    with pytest.raises(BusinessRuleError, match="материал"):
        service.add_component(1, BomComponentAdd(component_item_id=2, quantity=Decimal("1")))


def test_item_cannot_contain_itself():
    pizza = SimpleNamespace(id=5, name="Пицца", item_type_id=3)
    service = make_fake_service([pizza])
    with pytest.raises(BusinessRuleError, match="собственный состав"):
        service.add_component(5, BomComponentAdd(component_item_id=5, quantity=Decimal("1")))


def test_unknown_item_is_not_found():
    service = make_fake_service([])
    with pytest.raises(NotFoundError):
        service.add_component(42, BomComponentAdd(component_item_id=1, quantity=Decimal("1")))
