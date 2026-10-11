from decimal import Decimal
from typing import ClassVar, Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class PackagingType(SQLModel, table=True):
    """Классификатор видов тары (дерево)."""

    __tablename__: ClassVar[str] = "packaging_type"

    id: Optional[int] = Field(default=None, primary_key=True)
    parent_id: Optional[int] = Field(default=None, foreign_key="packaging_type.id")
    name: str = Field(max_length=255)


class Packaging(SQLModel, table=True):
    """Конкретная тара с габаритами."""

    __tablename__: ClassVar[str] = "packaging"

    id: Optional[int] = Field(default=None, primary_key=True)
    packaging_type_id: Optional[int] = Field(default=None, foreign_key="packaging_type.id")
    weight: Optional[Decimal] = Field(default=None, decimal_places=3, max_digits=10)
    length: Optional[Decimal] = Field(default=None, decimal_places=3, max_digits=10)
    width: Optional[Decimal] = Field(default=None, decimal_places=3, max_digits=10)
    height: Optional[Decimal] = Field(default=None, decimal_places=3, max_digits=10)
    inner_volume: Optional[Decimal] = Field(default=None, decimal_places=3, max_digits=10)


class PackagingNorm(SQLModel, table=True):
    """Норматив: количество изделий в упаковке."""

    __tablename__: ClassVar[str] = "packaging_norm"
    __table_args__ = (UniqueConstraint("item_id", "packaging_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="item.id")
    packaging_id: int = Field(foreign_key="packaging.id")
    quantity: Decimal = Field(decimal_places=3, max_digits=18)
    gost_number: Optional[str] = Field(default=None, max_length=50)
