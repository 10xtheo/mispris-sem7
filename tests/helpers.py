"""Построитель тестовых данных предметной области «Сервис доставки готовой еды»."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from sqlmodel import Session

from src.models.classifiers import ItemClassifier
from src.models.enums import EnumValue
from src.models.items import Item, UnitQuantity
from src.models.units import UnitSimple
from src.repository.bom_repository import (
    ItemBomRepository,
    ItemCatalogRepository,
    ItemChangeRepository,
    ModificationRepository,
)
from src.repository.classifier_repository import ItemClassifierRepository
from src.repository.enum_repository import EnumValueRepository
from src.repository.item_repository import ItemRepository, UnitQuantityRepository
from src.schemas.bom import BomComponentAdd
from src.services.bom_service import BomService

D = Decimal


def make_service(session: Session) -> BomService:
    return BomService(
        items=ItemRepository(session),
        boms=ItemBomRepository(session),
        changes=ItemChangeRepository(session),
        modifications=ModificationRepository(session),
        enum_values=EnumValueRepository(session),
        units=UnitQuantityRepository(session),
        classifiers=ItemClassifierRepository(session),
        catalog=ItemCatalogRepository(session),
    )


@dataclass
class Catalog:
    """Классификатор, ЕИ и изделия; помогает собирать спецификации в тестах."""

    session: Session
    units: dict[str, UnitSimple] = field(default_factory=dict)
    classes: dict[str, ItemClassifier] = field(default_factory=dict)
    items: dict[str, Item] = field(default_factory=dict)
    uq: dict[tuple[str, str], UnitQuantity] = field(default_factory=dict)
    _n: int = 0

    def __post_init__(self) -> None:
        self.service = make_service(self.session)
        self.enums = EnumValueRepository(self.session)

    # -- справочники
    def item_type(self, code: str) -> EnumValue:
        ev = self.enums.get_by_codes("item_type", code)
        assert ev is not None, code
        return ev

    def unit(self, symbol: str, code: Optional[str] = None) -> UnitSimple:
        if symbol not in self.units:
            u = UnitSimple(code=code or f"U{len(self.units)}{symbol}"[:10], name=symbol, cond_symbol_1=symbol)
            self.session.add(u)
            self.session.flush()
            self.units[symbol] = u
        return self.units[symbol]

    def cls(self, name: str, parent: Optional[str] = None) -> ItemClassifier:
        if name not in self.classes:
            c = ItemClassifier(name=name, parent_id=self.classes[parent].id if parent else None)
            self.session.add(c)
            self.session.flush()
            self.classes[name] = c
        return self.classes[name]

    def item(
        self,
        key: str,
        type_code: str,
        cls: Optional[str] = None,
        base_unit: str = "кг",
        extra_units: Optional[dict[str, str]] = None,
    ) -> Item:
        """Изделие с базовой ЕИ и дополнительными ЕИ {символ: коэффициент к базовой}."""
        self._n += 1
        it = Item(
            number=f"T-{self._n:03d}",
            name=key,
            item_type_id=self.item_type(type_code).id,
            item_class_id=self.classes[cls].id if cls else None,
        )
        self.session.add(it)
        self.session.flush()
        self.items[key] = it
        self._add_uq(key, base_unit, "1", is_base=True)
        for sym, coef in (extra_units or {}).items():
            self._add_uq(key, sym, coef, is_base=False)
        return it

    def _add_uq(self, key: str, symbol: str, coef: str, is_base: bool) -> UnitQuantity:
        uq = UnitQuantity(
            item_id=self.items[key].id, unit_simple_id=self.unit(symbol).id, coefficient=D(coef), is_base=is_base
        )
        self.session.add(uq)
        self.session.flush()
        self.uq[(key, symbol)] = uq
        return uq

    def add(
        self,
        parent: str,
        component: str,
        qty: str,
        unit: Optional[str] = None,
        for_qty: str = "1",
        is_base: bool = True,
        order: int = 0,
    ):
        return self.service.add_component(
            self.items[parent].id,  # type: ignore[arg-type]
            BomComponentAdd(
                component_item_id=self.items[component].id,  # type: ignore[arg-type]
                quantity=D(qty),
                for_quantity=D(for_qty),
                unit_quantity_id=self.uq[(component, unit)].id if unit else None,
                is_base=is_base,
                order_number=order,
            ),
        )

    def id(self, key: str) -> int:
        return self.items[key].id  # type: ignore[return-value]


def build_food_catalog(session: Session) -> Catalog:
    """Каталог сервиса доставки еды: сырьё → полуфабрикаты → блюда → наборы.

    Нормы на 1 «Комбо на двоих» (2 пиццы + пармезан 30 г):
        Мука 0.3 кг, Вода 0.19 л, Дрожжи 0.01 кг, Томаты 0.192 кг,
        Базилик 0.0116 кг, Моцарелла 0.24 кг, Пармезан 0.03 кг.
    """
    c = Catalog(session)
    c.cls("Продукты")
    c.cls("Сырьё", "Продукты")
    c.cls("Мука и крупы", "Сырьё")
    c.cls("Молочные продукты", "Сырьё")
    c.cls("Сыры", "Молочные продукты")
    c.cls("Овощи", "Сырьё")
    c.cls("Специи и зелень", "Сырьё")
    c.cls("Напитки и вода", "Сырьё")
    c.cls("Полуфабрикаты", "Продукты")
    c.cls("Блюда", "Продукты")
    c.cls("Пицца", "Блюда")
    c.cls("Наборы", "Продукты")

    grams = {"г": "0.001"}
    c.item("Мука пшеничная", "material", "Мука и крупы")
    c.item("Вода питьевая", "material", "Напитки и вода", base_unit="л")
    c.item("Дрожжи", "material", "Мука и крупы", extra_units=grams)
    c.item("Моцарелла", "material", "Сыры", extra_units=grams)
    c.item("Пармезан", "material", "Сыры", extra_units=grams)
    c.item("Томаты", "material", "Овощи")
    c.item("Базилик", "material", "Специи и зелень", extra_units=grams)
    c.item("Халапеньо", "material", "Овощи", extra_units=grams)
    c.item("Тесто для пиццы", "detail", "Полуфабрикаты")
    c.item("Соус томатный", "detail", "Полуфабрикаты")
    c.item("Пицца Маргарита", "assembly", "Пицца", base_unit="шт")
    c.item("Комбо на двоих", "complex", "Наборы", base_unit="шт")

    # Тесто: на 1 кг теста
    c.add("Тесто для пиццы", "Мука пшеничная", "0.6", order=1)
    c.add("Тесто для пиццы", "Вода питьевая", "0.38", order=2)
    c.add("Тесто для пиццы", "Дрожжи", "20", unit="г", order=3)
    # Соус: на 1 кг соуса (норма базилика дана на 10 кг: 100 г / 10 кг)
    c.add("Соус томатный", "Томаты", "1.2", order=1)
    c.add("Соус томатный", "Базилик", "100", unit="г", for_qty="10", order=2)
    # Пицца: на 1 шт
    c.add("Пицца Маргарита", "Тесто для пиццы", "0.25", order=1)
    c.add("Пицца Маргарита", "Соус томатный", "0.08", order=2)
    c.add("Пицца Маргарита", "Моцарелла", "120", unit="г", order=3)
    c.add("Пицца Маргарита", "Базилик", "5", unit="г", order=4)
    # Комбо: на 1 набор
    c.add("Комбо на двоих", "Пицца Маргарита", "2", order=1)
    c.add("Комбо на двоих", "Пармезан", "30", unit="г", order=2)
    return c
