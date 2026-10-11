from typing import ClassVar, Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class SxdRole(SQLModel, table=True):
    """Справочник ролей участников ХО (Отправитель, Получатель, Плательщик...)."""

    __tablename__: ClassVar[str] = "sxd_role"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, unique=True)
    # Парная роль: Отправитель ↔ Получатель
    inverse_id: Optional[int] = Field(default=None, foreign_key="sxd_role.id")


class AvailableRoles(SQLModel, table=True):
    """Допустимые роли для типа ХО с кратностью (min/max)."""

    __tablename__: ClassVar[str] = "available_roles"
    __table_args__ = (UniqueConstraint("ho_type_id", "role_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    ho_type_id: int = Field(foreign_key="ho_classifier.id")
    role_id: int = Field(foreign_key="sxd_role.id")
    min_count: int = Field(default=0, ge=0)
    max_count: Optional[int] = Field(default=None, ge=0)
    is_required: bool = Field(default=False)
