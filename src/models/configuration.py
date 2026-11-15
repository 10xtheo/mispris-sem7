"""Модель №7: вариант является изделием, метаданные расширяют Item."""
from datetime import date
from decimal import Decimal
from typing import ClassVar, Optional

from sqlalchemy import CheckConstraint, Column, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class ItemConfiguration(SQLModel, table=True):
    __tablename__: ClassVar[str] = "item_configuration"
    __table_args__ = (CheckConstraint(
        "(kind = 'template' AND template_id IS NULL) OR (kind = 'variant' AND template_id IS NOT NULL AND template_id <> item_id)",
        name="ck_item_configuration_kind"),)
    item_id: int = Field(primary_key=True, foreign_key="item.id")
    kind: str = Field(max_length=20)
    template_id: Optional[int] = Field(default=None, foreign_key="item.id")


class ClassConfigurationParameter(SQLModel, table=True):
    __tablename__: ClassVar[str] = "class_configuration_parameter"
    __table_args__ = (UniqueConstraint("class_id", "parameter_id"), CheckConstraint(
        "min_value IS NULL OR max_value IS NULL OR min_value <= max_value", name="ck_configuration_range"))
    id: Optional[int] = Field(default=None, primary_key=True)
    class_id: int = Field(foreign_key="item_classifier.id")
    parameter_id: int = Field(foreign_key="parameter.id")
    flag_conf: bool = True
    required: bool = True
    display_order: int = 0
    min_value: Optional[Decimal] = Field(default=None, max_digits=18, decimal_places=6)
    max_value: Optional[Decimal] = Field(default=None, max_digits=18, decimal_places=6)


class VariantParameterValue(SQLModel, table=True):
    __tablename__: ClassVar[str] = "variant_parameter_value"
    item_id: int = Field(primary_key=True, foreign_key="item.id")
    parameter_id: int = Field(primary_key=True, foreign_key="parameter.id")
    value: object = Field(sa_column=Column(JSONB, nullable=False))


class ConfigurationFunction(SQLModel, table=True):
    __tablename__: ClassVar[str] = "configuration_function"
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(max_length=50, unique=True)
    name: str = Field(max_length=255)
    definition: dict = Field(sa_column=Column(JSONB, nullable=False))


class ConfigurationConstraint(SQLModel, table=True):
    __tablename__: ClassVar[str] = "configuration_constraint"
    __table_args__ = (UniqueConstraint("template_id", "name"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    template_id: int = Field(foreign_key="item.id")
    name: str = Field(max_length=255)
    expression: dict = Field(sa_column=Column(JSONB, nullable=False))


class CustomerOrder(SQLModel, table=True):
    __tablename__: ClassVar[str] = "customer_order"
    __table_args__ = (CheckConstraint("status IN ('draft', 'agreed')", name="ck_customer_order_status"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    number: str = Field(max_length=50, unique=True)
    customer: str = Field(max_length=255)
    order_date: date
    status: str = Field(default="draft", max_length=20)
    ho_id: Optional[int] = Field(default=None, foreign_key="ho.id")


class CustomerOrderPosition(SQLModel, table=True):
    __tablename__: ClassVar[str] = "customer_order_position"
    __table_args__ = (UniqueConstraint("order_id", "number"), CheckConstraint("quantity > 0 AND number > 0", name="ck_order_position_quantity"))
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="customer_order.id")
    number: int
    item_id: int = Field(foreign_key="item.id")
    quantity: Decimal = Field(max_digits=18, decimal_places=6)
