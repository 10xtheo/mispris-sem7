from typing import Optional, Sequence

from sqlmodel import Session, select

from src.models.ho import Document
from src.models.param_values import DocParameterValue
from src.repository.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    def __init__(self, session: Session) -> None:
        super().__init__(Document, session)

    def get_by_ho(self, ho_id: int) -> Sequence[Document]:
        result = self.session.exec(
            select(Document).where(Document.ho_id == ho_id)
        )
        return result.all()


class DocParameterValueRepository(BaseRepository[DocParameterValue]):
    def __init__(self, session: Session) -> None:
        super().__init__(DocParameterValue, session)

    def get_by_document(self, document_id: int) -> Sequence[DocParameterValue]:
        result = self.session.exec(
            select(DocParameterValue).where(DocParameterValue.document_id == document_id)
        )
        return result.all()

    def get_by_doc_and_class_param(self, document_id: int, doc_class_param_id: int) -> Optional[DocParameterValue]:
        result = self.session.exec(
            select(DocParameterValue).where(
                DocParameterValue.document_id == document_id,
                DocParameterValue.doc_class_param_id == doc_class_param_id,
            )
        )
        return result.first()
