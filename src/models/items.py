from decimal import Decimal
from typing import ClassVar, Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class Item(SQLModel, table=True):
    """Номенклатурная позиция (изделие, материал).

    item_type_id — тип изделия (enum_type 'item_type': материал / деталь /
    сборочная единица / комплекс). base_item_id — для модификации ссылка на
    базовое изделие, чью базовую спецификацию она наследует.
    """

    __tablename__: ClassVar[str] = "item"

    id: Optional[int] = Field(default=None, primary_key=True)
    item_class_id: Optional[int] = Field(default=None, foreign_key="item_classifier.id")
    number: str = Field(max_length=50, unique=True)
    article: Optional[str] = Field(default=None, max_length=100)
    name: str = Field(max_length=500)
    item_type_id: Optional[int] = Field(default=None, foreign_key="enum_value.id")
    base_item_id: Optional[int] = Field(default=None, foreign_key="item.id")


class UnitQuantity(SQLModel, table=True):
    """Допустимые ЕИ количества для изделия. is_base — базовая ЕИ хранения."""

    __tablename__: ClassVar[str] = "unit_quantity"
    __table_args__ = (UniqueConstraint("item_id", "unit_simple_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="item.id")
    unit_simple_id: int = Field(foreign_key="unit_simple.id")
    coefficient: Decimal = Field(default=Decimal("1"), decimal_places=6, max_digits=18)
    is_base: bool = Field(default=False)


class ItemBatch(SQLModel, table=True):
    """Учётная партия изделий. parent_id — для Выделить/Объединить."""

    __tablename__: ClassVar[str] = "item_batch"

    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="item.id")
    parent_id: Optional[int] = Field(default=None, foreign_key="item_batch.id")
    quantity: Decimal = Field(decimal_places=3, max_digits=18)
