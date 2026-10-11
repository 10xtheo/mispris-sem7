from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel


class EnumTypeCreate(SQLModel):
    code: str
    name: str


class EnumTypeUpdate(SQLModel):
    code: Optional[str] = None
    name: Optional[str] = None


class EnumTypeRead(SQLModel):
    id: int
    code: str
    name: str


class EnumValueCreate(SQLModel):
    enum_type_id: int
    order_number: int
    code: Optional[str] = None
    name: str
    numeric_value: Optional[Decimal] = None
    unit_id: Optional[int] = None


class EnumValueUpdate(SQLModel):
    order_number: Optional[int] = None
    code: Optional[str] = None
    name: Optional[str] = None
    numeric_value: Optional[Decimal] = None
    unit_id: Optional[int] = None


class EnumValueRead(SQLModel):
    id: int
    enum_type_id: int
    order_number: int
    code: Optional[str]
    name: str
    numeric_value: Optional[Decimal]
    unit_id: Optional[int]
