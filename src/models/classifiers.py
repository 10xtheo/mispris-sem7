from typing import ClassVar, Optional

from sqlmodel import Field, SQLModel


class SxdClassifier(SQLModel, table=True):
    """Иерархия классов СХД (например, Поставщики > Зарубежные)."""

    __tablename__: ClassVar[str] = "sxd_classifier"

    id: Optional[int] = Field(default=None, primary_key=True)
    parent_id: Optional[int] = Field(default=None, foreign_key="sxd_classifier.id")
    name: str = Field(max_length=255)
    code: str = Field(max_length=50, unique=True)


class HoClassifier(SQLModel, table=True):
    """Иерархия типов ХО (например, ХО > Перемещение > Отгрузка)."""

    __tablename__: ClassVar[str] = "ho_classifier"

    id: Optional[int] = Field(default=None, primary_key=True)
    parent_id: Optional[int] = Field(default=None, foreign_key="ho_classifier.id")
    name: str = Field(max_length=255)
    code: str = Field(max_length=50, unique=True)


class DocumentClassifier(SQLModel, table=True):
    """Иерархия типов документов (например, Документ > ТТН)."""

    __tablename__: ClassVar[str] = "document_classifier"

    id: Optional[int] = Field(default=None, primary_key=True)
    parent_id: Optional[int] = Field(default=None, foreign_key="document_classifier.id")
    name: str = Field(max_length=255)
    code: str = Field(max_length=50, unique=True)


class ItemClassifier(SQLModel, table=True):
    """Иерархия номенклатурных групп (например, Металлопрокат > Листовой)."""

    __tablename__: ClassVar[str] = "item_classifier"

    id: Optional[int] = Field(default=None, primary_key=True)
    parent_id: Optional[int] = Field(default=None, foreign_key="item_classifier.id")
    number: Optional[str] = Field(default=None, max_length=50)
    name: str = Field(max_length=255)
