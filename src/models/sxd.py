from typing import ClassVar, Optional

from sqlmodel import Field, SQLModel


class Sxd(SQLModel, table=True):
    """Субъект хозяйственной деятельности: ЮЛ, ИП или подразделение."""

    __tablename__: ClassVar[str] = "sxd"

    id: Optional[int] = Field(default=None, primary_key=True)
    sxd_class_id: Optional[int] = Field(default=None, foreign_key="sxd_classifier.id")
    entity_type_id: int = Field(foreign_key="enum_value.id")
    name: str = Field(max_length=500)
    okpo: Optional[str] = Field(default=None, max_length=20)
