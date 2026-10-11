from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel

from src.schemas.items import ItemRead


class PricelistSetCreate(SQLModel):
    parent_id: Optional[int] = None


class PricelistSetRead(SQLModel):
    id: int
    parent_id: Optional[int]


class PricelistCreate(SQLModel):
    pricelist_set_id: int
    item_id: int
    article: Optional[str] = None
    price: Decimal


class PricelistRead(SQLModel):
    id: int
    pricelist_set_id: int
    item_id: int
    article: Optional[str]
    price: Decimal


class HoPositionCreate(SQLModel):
    position_list_id: int
    item_id: int
    quantity: Decimal
    price: Optional[Decimal] = None
    unit_quantity_id: Optional[int] = None
    batch_id: Optional[int] = None
    packaging_id: Optional[int] = None
    pricelist_id: Optional[int] = None
    quantity_places: Optional[int] = None
    weight_netto: Optional[Decimal] = None


class HoPositionUpdate(SQLModel):
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    unit_quantity_id: Optional[int] = None
    batch_id: Optional[int] = None
    packaging_id: Optional[int] = None
    pricelist_id: Optional[int] = None
    quantity_places: Optional[int] = None
    weight_netto: Optional[Decimal] = None


class HoPositionRead(SQLModel):
    id: int
    position_list_id: int
    item_id: int
    quantity: Decimal
    price: Optional[Decimal]
    unit_quantity_id: Optional[int]
    batch_id: Optional[int]
    packaging_id: Optional[int]
    pricelist_id: Optional[int]
    quantity_places: Optional[int]
    weight_netto: Optional[Decimal]
    total_amount: Optional[Decimal]  # вычисляется базой данных
    item: Optional[ItemRead] = None
