from typing import ClassVar, Optional

from sqlmodel import Field, SQLModel


class Parameter(SQLModel, table=True):
    """Глобальный справочник параметров. Тип задаётся через param_type_id → EnumValue."""

    __tablename__: ClassVar[str] = "parameter"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(max_length=50, unique=True)
    name: str = Field(max_length=255)
    param_type_id: int = Field(foreign_key="enum_value.id")
    enum_type_id: Optional[int] = Field(default=None, foreign_key="enum_type.id")
    unit_simple_id: Optional[int] = Field(default=None, foreign_key="unit_simple.id")
