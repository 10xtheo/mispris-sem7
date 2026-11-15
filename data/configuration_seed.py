"""Воспроизводимый пример №7; вызывается общим сидером на демонстрационной БД."""
from datetime import date
from copy import deepcopy
from decimal import Decimal

from sqlmodel import select

from src.models import Item, ItemClassifier, Parameter, EnumType, EnumValue, UnitQuantity, UnitSimple, TechnologyTemplate, Pricelist, PricelistSet
from src.repository.configuration_repository import ConfigurationRepository
from src.services.configuration_service import ConfigurationService
from src.schemas.configuration import ClassParameterInput, ConstraintInput, FunctionInput, VariantInput, OrderInput, PositionInput
from src.repository.technology_repository import TechnologyRepository
from src.services.technology_service import TechnologyService
from src.schemas.technology import TemplateCreate, TemplateApply, OperationCreate


def seed_configuration(session):
    repo = ConfigurationRepository(session)
    svc = ConfigurationService(repo)
    add = repo.save
    number = session.exec(select(EnumValue).join(EnumType).where(EnumType.code == "param_type", EnumValue.code == "number")).one()
    enum = session.exec(select(EnumValue).join(EnumType).where(EnumType.code == "param_type", EnumValue.code == "enum")).one()
    item_type = session.exec(select(EnumValue).join(EnumType).where(EnumType.code == "item_type", EnumValue.code == "assembly")).one()
    cm = add(UnitSimple(code="CMT", name="Сантиметр", cond_symbol_1="см"))
    grams = session.exec(select(UnitSimple).where(UnitSimple.code == "GRM")).one()
    piece = session.exec(select(UnitSimple).where(UnitSimple.code == "PCE")).one()
    top_type = add(EnumType(code="pizza_topping", name="Добавка пиццы"))
    basil = add(EnumValue(enum_type_id=top_type.id, order_number=1, code="basil", name="Базилик"))
    chili = add(EnumValue(enum_type_id=top_type.id, order_number=2, code="chili", name="Халапеньо"))
    cls = add(ItemClassifier(name="Пиццы с конфигуратором", number="CONF-7"))
    template = add(Item(number="PZ-CONF", name="Пицца по индивидуальному заказу", item_class_id=cls.id, item_type_id=item_type.id))
    add(UnitQuantity(item_id=template.id, unit_simple_id=piece.id, is_base=True, coefficient=1))
    for code, name, typ, unit, enum_id, minimum, maximum in (
        ("diameter", "Диаметр", number.id, cm.id, None, 30, 35),
        ("cheese_g", "Масса сыра", number.id, grams.id, None, 90, 210),
        ("topping", "Добавка", enum.id, None, top_type.id, None, None),
    ):
        parameter = add(Parameter(code=code, name=name, param_type_id=typ, unit_simple_id=unit, enum_type_id=enum_id))
        svc.assign_parameter(cls.id, ClassParameterInput(parameter_id=parameter.id, min_value=minimum, max_value=maximum))
    svc.enable_template(template.id)

    def const(value): return {"kind": "const", "value": value}
    def par(name): return {"kind": "param", "name": name}
    def op(operator, *args): return {"kind": "op", "op": operator, "args": list(args)}
    ratio = op("/", par("mass"), par("size"))
    svc.save_function(FunctionInput(code="CheeseRatio", name="Проверка нормы сыра", definition={
        "parameters": {"mass": "number", "size": "number"}, "result": "bool",
        "body": op("and", op("ge", ratio, const(3)), op("le", ratio, const(6)))}))
    svc.save_constraint(template.id, ConstraintInput(name="От 3 до 6 г сыра на сантиметр диаметра", expression={
        "kind": "call", "function": "CheeseRatio", "args": {"mass": par("cheese_g"), "size": par("diameter")}}))
    svc.save_constraint(template.id, ConstraintInput(name="Диаметр 30 или 35 см", expression=op("in", par("diameter"), const(30), const(35))))
    # Типовая технология №6 применяется к конкретному варианту с его собственными нормами.
    technology = TechnologyService(TechnologyRepository(session))
    material_type = session.exec(select(EnumValue).join(EnumType).where(EnumType.code == "item_type", EnumValue.code == "material")).one()
    box = add(Item(number="PK-CONF-35", name="Коробка для пиццы 35 см", item_type_id=material_type.id))
    add(UnitQuantity(item_id=box.id, unit_simple_id=piece.id, is_base=True, coefficient=1))
    technology.save_operation(box.id, OperationCreate(number=10, name="Закупка", kind="purchase", is_output=True))
    price_set = session.exec(select(PricelistSet)).first()
    add(Pricelist(pricelist_set_id=price_set.id, item_id=box.id, price=Decimal("35")))
    original = session.exec(select(TechnologyTemplate).where(TechnologyTemplate.code == "PIZZA-30")).one()
    definition = deepcopy(original.definition)
    definition["parameters"] += ["dough_kg", "sauce_kg"]
    for entry in definition["steps"][0]["inputs"]:
        if entry.get("input_key") in ("dough", "sauce"):
            entry["quantity"] = {"factors": {entry["input_key"] + "_kg": 1}}
    production_template = technology.create_template(TemplateCreate(code="PIZZA-CONF", name="Пицца выбранного размера", definition=definition))

    def resource(name, symbol=None):
        item = session.exec(select(Item).where(Item.name == name)).one()
        output = technology.repo.output(item.id)
        unit = next((u for u in repo.rows(UnitQuantity, item_id=item.id)
                     if symbol and repo.get(UnitSimple, u.unit_simple_id).cond_symbol_1 == symbol), None)
        return {"operation_id": output.id, "unit_quantity_id": unit.id if unit else None}

    variants = []
    for suffix, diameter, cheese, topping in (("30", 30, 130, basil), ("35", 35, 160, chili)):
        values = dict(diameter=diameter, cheese_g=cheese, topping=topping.id)
        result = svc.create_variant(template.id, VariantInput(number="PZ-CONF-" + suffix, name="Пицца " + suffix + " см", values=values))
        variant = result["item"]
        scale = (Decimal(diameter) / 30) ** 2
        technology.apply_template(variant.id, production_template.id, TemplateApply(
            parameters={"cheese_g": cheese, "topping_g": 5 if topping.id == basil.id else 30,
                        "baking_minutes": 7 if diameter == 30 else 9,
                        "dough_kg": (Decimal("0.25") * scale).quantize(Decimal("0.000001")),
                        "sauce_kg": (Decimal("0.08") * scale).quantize(Decimal("0.000001"))},
            resources={"dough": resource("Тесто для пиццы"), "sauce": resource("Соус томатный"),
                       "cheese": resource("Моцарелла", "г"), "topping": resource("Базилик свежий" if topping.id == basil.id else "Халапеньо", "г"),
                       "box": resource(f"Коробка для пиццы {diameter} см")},
        ))
        variants.append(variant)
    order = svc.create_order(OrderInput(number="ORDER-007", customer="Иван Иванов", order_date=date(2026, 11, 15)))
    for index, variant in enumerate(variants, 1):
        svc.put_position(order.id, PositionInput(number=index, item_id=variant.id, quantity=2 if index == 1 else 1))
    return {"template_id": template.id, "order_id": order.id, "variant_ids": [item.id for item in variants]}
