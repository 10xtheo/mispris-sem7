from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlmodel import SQLModel

from src.schemas.enums import EnumValueRead
from src.schemas.parameters import ParameterRead
from src.schemas.roles import SxdRoleRead
from src.schemas.sxd import SxdRead


# ---- HoClassParameter (шаблон параметров типа ХО) ----

class HoClassParameterCreate(SQLModel):
    ho_type_id: int
    parameter_id: int
    display_order: int = 0
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None


class HoClassParameterRead(SQLModel):
    id: int
    ho_type_id: int
    parameter_id: int
    display_order: int
    min_value: Optional[Decimal]
    max_value: Optional[Decimal]
    parameter: Optional[ParameterRead] = None


# ---- DocClassParameter ----

class DocClassParameterCreate(SQLModel):
    doc_type_id: int
    parameter_id: int
    display_order: int = 0
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None


class DocClassParameterRead(SQLModel):
    id: int
    doc_type_id: int
    parameter_id: int
    display_order: int
    min_value: Optional[Decimal]
    max_value: Optional[Decimal]


# ---- Ho (экземпляр ХО) ----

class HoCreate(SQLModel):
    ho_type_id: int
    document_number: Optional[str] = None
    op_date: date
    amount: Optional[Decimal] = None


class HoUpdate(SQLModel):
    document_number: Optional[str] = None
    op_date: Optional[date] = None
    amount: Optional[Decimal] = None


class HoRead(SQLModel):
    id: int
    ho_type_id: int
    document_number: Optional[str]
    op_date: date
    amount: Optional[Decimal]


class HoParameterValueRead(SQLModel):
    """Значение параметра ХО с метаданными параметра."""

    id: int
    ho_id: int
    ho_class_param_id: int
    value_str: Optional[str]
    value_int: Optional[int]
    value_real: Optional[Decimal]
    value_dt: Optional[datetime]
    value_enum_id: Optional[int]
    parameter_name: Optional[str] = None
    parameter_code: Optional[str] = None


class HoParameterValueWrite(SQLModel):
    """Запись значения параметра ХО. Заполняется только одно поле в зависимости от типа."""

    value_str: Optional[str] = None
    value_int: Optional[int] = None
    value_real: Optional[Decimal] = None
    value_dt: Optional[datetime] = None
    value_enum_id: Optional[int] = None


class SxdRoleInHoCreate(SQLModel):
    sxd_id: int
    role_id: int


class SxdRoleInHoRead(SQLModel):
    id: int
    ho_id: int
    sxd_id: int
    role_id: int
    sxd: Optional[SxdRead] = None
    role: Optional[SxdRoleRead] = None


class HoReadFull(SQLModel):
    """Полное представление ХО со всеми характеристиками."""

    id: int
    ho_type_id: int
    document_number: Optional[str]
    op_date: date
    amount: Optional[Decimal]
    parameters: List[HoParameterValueRead] = []
    roles: List[SxdRoleInHoRead] = []


# ---- Document ----

class DocumentCreate(SQLModel):
    doc_type_id: int
    ho_id: Optional[int] = None
    reg_number: Optional[str] = None
    doc_date: Optional[date] = None


class DocumentUpdate(SQLModel):
    reg_number: Optional[str] = None
    doc_date: Optional[date] = None
    ho_id: Optional[int] = None


class DocumentRead(SQLModel):
    id: int
    doc_type_id: int
    ho_id: Optional[int]
    reg_number: Optional[str]
    doc_date: Optional[date]


class DocParameterValueRead(SQLModel):
    id: int
    document_id: int
    doc_class_param_id: int
    value_str: Optional[str]
    value_int: Optional[int]
    value_real: Optional[Decimal]
    value_dt: Optional[datetime]
    value_enum_id: Optional[int]


class DocParameterValueWrite(SQLModel):
    value_str: Optional[str] = None
    value_int: Optional[int] = None
    value_real: Optional[Decimal] = None
    value_dt: Optional[datetime] = None
    value_enum_id: Optional[int] = None


# ---- HoSearch ----

class HoSearchParams(SQLModel):
    """Параметры поиска ХО по классу и значениям параметров."""

    ho_type_id: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    document_number: Optional[str] = None
    skip: int = 0
    limit: int = 100
