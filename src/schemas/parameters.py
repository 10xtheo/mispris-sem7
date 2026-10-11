from typing import Optional

from sqlmodel import SQLModel


class ParameterCreate(SQLModel):
    code: str
    name: str
    param_type_id: int
    enum_type_id: Optional[int] = None
    unit_simple_id: Optional[int] = None


class ParameterUpdate(SQLModel):
    code: Optional[str] = None
    name: Optional[str] = None
    param_type_id: Optional[int] = None
    enum_type_id: Optional[int] = None
    unit_simple_id: Optional[int] = None


class ParameterRead(SQLModel):
    id: int
    code: str
    name: str
    param_type_id: int
    enum_type_id: Optional[int]
    unit_simple_id: Optional[int]
