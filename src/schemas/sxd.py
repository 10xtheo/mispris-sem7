from typing import Optional

from sqlmodel import SQLModel


class SxdCreate(SQLModel):
    sxd_class_id: Optional[int] = None
    entity_type_id: int
    name: str
    okpo: Optional[str] = None


class SxdUpdate(SQLModel):
    sxd_class_id: Optional[int] = None
    entity_type_id: Optional[int] = None
    name: Optional[str] = None
    okpo: Optional[str] = None


class SxdRead(SQLModel):
    id: int
    sxd_class_id: Optional[int]
    entity_type_id: int
    name: str
    okpo: Optional[str]
