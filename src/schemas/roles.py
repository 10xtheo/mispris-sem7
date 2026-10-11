from typing import Optional

from sqlmodel import SQLModel


class SxdRoleCreate(SQLModel):
    name: str
    inverse_id: Optional[int] = None


class SxdRoleUpdate(SQLModel):
    name: Optional[str] = None
    inverse_id: Optional[int] = None


class SxdRoleRead(SQLModel):
    id: int
    name: str
    inverse_id: Optional[int]


class AvailableRoleCreate(SQLModel):
    ho_type_id: int
    role_id: int
    min_count: int = 0
    max_count: Optional[int] = None
    is_required: bool = False


class AvailableRoleUpdate(SQLModel):
    min_count: Optional[int] = None
    max_count: Optional[int] = None
    is_required: Optional[bool] = None


class AvailableRoleRead(SQLModel):
    id: int
    ho_type_id: int
    role_id: int
    min_count: int
    max_count: Optional[int]
    is_required: bool
