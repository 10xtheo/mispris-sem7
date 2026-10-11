from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel


class UnitSimpleCreate(SQLModel):
    base_unit_id: Optional[int] = None
    coefficient: Decimal = Decimal("1")
    code: str
    name: str
    cond_symbol_1: Optional[str] = None
    cond_symbol_2: Optional[str] = None
    code_symbol_1: Optional[str] = None
    code_symbol_2: Optional[str] = None


class UnitSimpleUpdate(SQLModel):
    base_unit_id: Optional[int] = None
    coefficient: Optional[Decimal] = None
    code: Optional[str] = None
    name: Optional[str] = None
    cond_symbol_1: Optional[str] = None
    cond_symbol_2: Optional[str] = None
    code_symbol_1: Optional[str] = None
    code_symbol_2: Optional[str] = None


class UnitSimpleRead(SQLModel):
    id: int
    base_unit_id: Optional[int]
    coefficient: Decimal
    code: str
    name: str
    cond_symbol_1: Optional[str]
    cond_symbol_2: Optional[str]
    code_symbol_1: Optional[str]
    code_symbol_2: Optional[str]
