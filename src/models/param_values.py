from datetime import datetime
from decimal import Decimal
from typing import ClassVar, Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class HoParameterValue(SQLModel, table=True):
    """Значения параметров конкретной ХО. Заполняется после создания ХО."""

    __tablename__: ClassVar[str] = "ho_parameter_value"
    __table_args__ = (UniqueConstraint("ho_id", "ho_class_param_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    ho_id: int = Field(foreign_key="ho.id")
    ho_class_param_id: int = Field(foreign_key="ho_class_parameter.id")
    value_str: Optional[str] = Field(default=None, max_length=500)
    value_int: Optional[int] = None
    value_real: Optional[Decimal] = Field(default=None, decimal_places=6, max_digits=18)
    value_dt: Optional[datetime] = None
    value_enum_id: Optional[int] = Field(default=None, foreign_key="enum_value.id")


class DocParameterValue(SQLModel, table=True):
    """Значения параметров конкретного документа (серия ТТН, ставка НДС и т.д.)."""

    __tablename__: ClassVar[str] = "doc_parameter_value"
    __table_args__ = (UniqueConstraint("document_id", "doc_class_param_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="document.id")
    doc_class_param_id: int = Field(foreign_key="doc_class_parameter.id")
    value_str: Optional[str] = Field(default=None, max_length=500)
    value_int: Optional[int] = None
    value_real: Optional[Decimal] = Field(default=None, decimal_places=6, max_digits=18)
    value_dt: Optional[datetime] = None
    value_enum_id: Optional[int] = Field(default=None, foreign_key="enum_value.id")
