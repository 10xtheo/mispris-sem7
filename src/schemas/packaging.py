from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel


class PackagingTypeCreate(SQLModel):
    parent_id: Optional[int] = None
    name: str


class PackagingTypeUpdate(SQLModel):
    parent_id: Optional[int] = None
    name: Optional[str] = None


class PackagingTypeRead(SQLModel):
    id: int
    parent_id: Optional[int]
    name: str


class PackagingCreate(SQLModel):
    packaging_type_id: Optional[int] = None
    weight: Optional[Decimal] = None
    length: Optional[Decimal] = None
    width: Optional[Decimal] = None
    height: Optional[Decimal] = None
    inner_volume: Optional[Decimal] = None


class PackagingUpdate(SQLModel):
    packaging_type_id: Optional[int] = None
    weight: Optional[Decimal] = None
    length: Optional[Decimal] = None
    width: Optional[Decimal] = None
    height: Optional[Decimal] = None
    inner_volume: Optional[Decimal] = None


class PackagingRead(SQLModel):
    id: int
    packaging_type_id: Optional[int]
    weight: Optional[Decimal]
    length: Optional[Decimal]
    width: Optional[Decimal]
    height: Optional[Decimal]
    inner_volume: Optional[Decimal]


class PackagingNormCreate(SQLModel):
    item_id: int
    packaging_id: int
    quantity: Decimal
    gost_number: Optional[str] = None


class PackagingNormRead(SQLModel):
    id: int
    item_id: int
    packaging_id: int
    quantity: Decimal
    gost_number: Optional[str]
