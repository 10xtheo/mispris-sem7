from decimal import Decimal
from typing import ClassVar, Optional

from sqlmodel import Field, SQLModel


class UnitSimple(SQLModel, table=True):
    """Единица измерения (ОКЕИ). Поддерживает иерархию через base_unit_id."""

    __tablename__: ClassVar[str] = "unit_simple"

    id: Optional[int] = Field(default=None, primary_key=True)
    base_unit_id: Optional[int] = Field(default=None, foreign_key="unit_simple.id")
    coefficient: Decimal = Field(default=Decimal("1"), decimal_places=6, max_digits=18)
    code: str = Field(max_length=10, unique=True)
    name: str = Field(max_length=100)
    cond_symbol_1: Optional[str] = Field(default=None, max_length=20)
    cond_symbol_2: Optional[str] = Field(default=None, max_length=20)
    code_symbol_1: Optional[str] = Field(default=None, max_length=10)
    code_symbol_2: Optional[str] = Field(default=None, max_length=10)
