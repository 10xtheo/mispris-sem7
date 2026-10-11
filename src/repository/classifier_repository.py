from typing import Optional, Sequence

from sqlmodel import Session, select

from src.models.classifiers import DocumentClassifier, HoClassifier, ItemClassifier, SxdClassifier
from src.repository.base import BaseRepository


class SxdClassifierRepository(BaseRepository[SxdClassifier]):
    def __init__(self, session: Session) -> None:
        super().__init__(SxdClassifier, session)

    def get_children(self, parent_id: Optional[int]) -> Sequence[SxdClassifier]:
        result = self.session.exec(
            select(SxdClassifier).where(SxdClassifier.parent_id == parent_id)
        )
        return result.all()


class HoClassifierRepository(BaseRepository[HoClassifier]):
    def __init__(self, session: Session) -> None:
        super().__init__(HoClassifier, session)

    def get_children(self, parent_id: Optional[int]) -> Sequence[HoClassifier]:
        result = self.session.exec(
            select(HoClassifier).where(HoClassifier.parent_id == parent_id)
        )
        return result.all()

    def get_by_code(self, code: str) -> Optional[HoClassifier]:
        result = self.session.exec(select(HoClassifier).where(HoClassifier.code == code))
        return result.first()


class DocumentClassifierRepository(BaseRepository[DocumentClassifier]):
    def __init__(self, session: Session) -> None:
        super().__init__(DocumentClassifier, session)

    def get_children(self, parent_id: Optional[int]) -> Sequence[DocumentClassifier]:
        result = self.session.exec(
            select(DocumentClassifier).where(DocumentClassifier.parent_id == parent_id)
        )
        return result.all()


class ItemClassifierRepository(BaseRepository[ItemClassifier]):
    def __init__(self, session: Session) -> None:
        super().__init__(ItemClassifier, session)

    def get_children(self, parent_id: Optional[int]) -> Sequence[ItemClassifier]:
        result = self.session.exec(
            select(ItemClassifier).where(ItemClassifier.parent_id == parent_id)
        )
        return result.all()
