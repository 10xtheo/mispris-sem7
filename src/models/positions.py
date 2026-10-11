from decimal import Decimal
from typing import ClassVar, Optional

from sqlalchemy import Column, Computed, Numeric, UniqueConstraint
from sqlmodel import Field, SQLModel


class PricelistSet(SQLModel, table=True):
    """Группирующий список прейскурантов. parent_id — дополнение к базовому."""

    __tablename__: ClassVar[str] = "pricelist_set"

    id: Optional[int] = Field(default=None, primary_key=True)
    parent_id: Optional[int] = Field(default=None, foreign_key="pricelist_set.id")


class Pricelist(SQLModel, table=True):
    """Цена изделия в конкретном прейскуранте."""

    __tablename__: ClassVar[str] = "pricelist"
    __table_args__ = (UniqueConstraint("pricelist_set_id", "item_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    pricelist_set_id: int = Field(foreign_key="pricelist_set.id")
    item_id: int = Field(foreign_key="item.id")
    article: Optional[str] = Field(default=None, max_length=100)
    price: Decimal = Field(decimal_places=2, max_digits=18)


class PositionList(SQLModel, table=True):
    """Табличная часть ХО (контейнер строк позиций)."""

    __tablename__: ClassVar[str] = "position_list"

    id: Optional[int] = Field(default=None, primary_key=True)
    ho_id: int = Field(foreign_key="ho.id", unique=True)


class HoPosition(SQLModel, table=True):
    """Строка табличной части ХО. total_amount вычисляется автоматически (quantity * price)."""

    __tablename__: ClassVar[str] = "ho_position"

    id: Optional[int] = Field(default=None, primary_key=True)
    position_list_id: int = Field(foreign_key="position_list.id")
    item_id: int = Field(foreign_key="item.id")
    quantity: Decimal = Field(decimal_places=3, max_digits=18)
    price: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=18)
    unit_quantity_id: Optional[int] = Field(default=None, foreign_key="unit_quantity.id")
    batch_id: Optional[int] = Field(default=None, foreign_key="item_batch.id")
    packaging_id: Optional[int] = Field(default=None, foreign_key="packaging.id")
    pricelist_id: Optional[int] = Field(default=None, foreign_key="pricelist.id")
    quantity_places: Optional[int] = None
    weight_netto: Optional[Decimal] = Field(default=None, decimal_places=3, max_digits=12)
    # GENERATED ALWAYS AS (quantity * COALESCE(price, 0)) STORED
    total_amount: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(
            Numeric(18, 2),
            Computed("quantity * COALESCE(price, 0)", persisted=True),
        ),
    )
