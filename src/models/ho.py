from datetime import date
from decimal import Decimal
from typing import ClassVar, Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class HoClassParameter(SQLModel, table=True):
    """Параметры, назначенные типу ХО (шаблон)."""

    __tablename__: ClassVar[str] = "ho_class_parameter"
    __table_args__ = (UniqueConstraint("ho_type_id", "parameter_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    ho_type_id: int = Field(foreign_key="ho_classifier.id")
    parameter_id: int = Field(foreign_key="parameter.id")
    display_order: int = Field(default=0)
    min_value: Optional[Decimal] = Field(default=None, decimal_places=6, max_digits=18)
    max_value: Optional[Decimal] = Field(default=None, decimal_places=6, max_digits=18)


class DocClassParameter(SQLModel, table=True):
    """Параметры, назначенные типу документа (шаблон)."""

    __tablename__: ClassVar[str] = "doc_class_parameter"
    __table_args__ = (UniqueConstraint("doc_type_id", "parameter_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    doc_type_id: int = Field(foreign_key="document_classifier.id")
    parameter_id: int = Field(foreign_key="parameter.id")
    display_order: int = Field(default=0)
    min_value: Optional[Decimal] = Field(default=None, decimal_places=6, max_digits=18)
    max_value: Optional[Decimal] = Field(default=None, decimal_places=6, max_digits=18)


class Ho(SQLModel, table=True):
    """Экземпляр хозяйственной операции."""

    __tablename__: ClassVar[str] = "ho"

    id: Optional[int] = Field(default=None, primary_key=True)
    ho_type_id: int = Field(foreign_key="ho_classifier.id")
    document_number: Optional[str] = Field(default=None, max_length=100)
    op_date: date
    amount: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=18)


class Document(SQLModel, table=True):
    """Документ (ТТН, Требование-накладная и т.д.), привязанный к ХО."""

    __tablename__: ClassVar[str] = "document"

    id: Optional[int] = Field(default=None, primary_key=True)
    doc_type_id: int = Field(foreign_key="document_classifier.id")
    ho_id: Optional[int] = Field(default=None, foreign_key="ho.id")
    reg_number: Optional[str] = Field(default=None, max_length=100)
    doc_date: Optional[date] = None


class SxdRoleInHo(SQLModel, table=True):
    """Назначение СХД на роль в конкретной ХО."""

    __tablename__: ClassVar[str] = "sxd_role_in_ho"
    __table_args__ = (UniqueConstraint("ho_id", "sxd_id", "role_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    ho_id: int = Field(foreign_key="ho.id")
    sxd_id: int = Field(foreign_key="sxd.id")
    role_id: int = Field(foreign_key="sxd_role.id")
