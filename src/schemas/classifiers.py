from typing import List, Optional

from sqlmodel import SQLModel


# ---- SxdClassifier ----

class SxdClassifierCreate(SQLModel):
    parent_id: Optional[int] = None
    name: str
    code: str


class SxdClassifierUpdate(SQLModel):
    parent_id: Optional[int] = None
    name: Optional[str] = None
    code: Optional[str] = None


class SxdClassifierRead(SQLModel):
    id: int
    parent_id: Optional[int]
    name: str
    code: str


# ---- HoClassifier ----

class HoClassifierCreate(SQLModel):
    parent_id: Optional[int] = None
    name: str
    code: str


class HoClassifierUpdate(SQLModel):
    parent_id: Optional[int] = None
    name: Optional[str] = None
    code: Optional[str] = None


class HoClassifierRead(SQLModel):
    id: int
    parent_id: Optional[int]
    name: str
    code: str


class HoClassifierTree(SQLModel):
    """Узел дерева классификатора ХО с дочерними элементами."""

    id: int
    parent_id: Optional[int]
    name: str
    code: str
    children: List["HoClassifierTree"] = []


HoClassifierTree.model_rebuild()


# ---- DocumentClassifier ----

class DocumentClassifierCreate(SQLModel):
    parent_id: Optional[int] = None
    name: str
    code: str


class DocumentClassifierUpdate(SQLModel):
    parent_id: Optional[int] = None
    name: Optional[str] = None
    code: Optional[str] = None


class DocumentClassifierRead(SQLModel):
    id: int
    parent_id: Optional[int]
    name: str
    code: str


# ---- ItemClassifier ----

class ItemClassifierCreate(SQLModel):
    parent_id: Optional[int] = None
    number: Optional[str] = None
    name: str


class ItemClassifierUpdate(SQLModel):
    parent_id: Optional[int] = None
    number: Optional[str] = None
    name: Optional[str] = None


class ItemClassifierRead(SQLModel):
    id: int
    parent_id: Optional[int]
    number: Optional[str]
    name: str
