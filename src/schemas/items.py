from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel


class ItemCreate(SQLModel):
    item_class_id: Optional[int] = None
    number: str
    article: Optional[str] = None
    name: str
    item_type_id: Optional[int] = None


class ItemUpdate(SQLModel):
    item_class_id: Optional[int] = None
    number: Optional[str] = None
    article: Optional[str] = None
    name: Optional[str] = None
    item_type_id: Optional[int] = None


class ItemRead(SQLModel):
    id: int
    item_class_id: Optional[int]
    number: str
    article: Optional[str]
    name: str
    item_type_id: Optional[int] = None
    base_item_id: Optional[int] = None


class UnitQuantityCreate(SQLModel):
    item_id: int
    unit_simple_id: int
    coefficient: Decimal = Decimal("1")
    is_base: bool = False


class UnitQuantityRead(SQLModel):
    id: int
    item_id: int
    unit_simple_id: int
    coefficient: Decimal
    is_base: bool


class ItemBatchCreate(SQLModel):
    item_id: int
    parent_id: Optional[int] = None
    quantity: Decimal


class ItemBatchRead(SQLModel):
    id: int
    item_id: int
    parent_id: Optional[int]
    quantity: Decimal
