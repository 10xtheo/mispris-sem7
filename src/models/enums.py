from decimal import Decimal
from typing import ClassVar, Optional

from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlmodel import Field, SQLModel


class EnumType(SQLModel, table=True):
    """Метакласс перечислений — например, 'Тип СХД', 'Тип параметра'."""

    __tablename__: ClassVar[str] = "enum_type"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(max_length=50, unique=True)
    name: str = Field(max_length=255)


class EnumValue(SQLModel, table=True):
    """Значение перечисления, привязанное к типу."""

    __tablename__: ClassVar[str] = "enum_value"
    __table_args__ = (UniqueConstraint("enum_type_id", "order_number"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    enum_type_id: int = Field(foreign_key="enum_type.id")
    order_number: int
    code: Optional[str] = Field(default=None, max_length=50)
    name: str = Field(max_length=255)
    numeric_value: Optional[Decimal] = Field(default=None, decimal_places=6, max_digits=18)
    # FK на unit_simple добавляется через use_alter (циклическая зависимость)
    unit_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey(
                "unit_simple.id",
                use_alter=True,
                name="fk_enum_value_unit",
                ondelete="SET NULL",
            ),
            nullable=True,
        ),
    )
