from typing import Sequence

from src.core.errors import BusinessRuleError, NotFoundError

from src.models.ho import Document
from src.models.param_values import DocParameterValue
from src.repository.document_repository import DocParameterValueRepository, DocumentRepository
from src.repository.enum_repository import EnumValueRepository
from src.repository.ho_repository import DocClassParameterRepository
from src.repository.parameter_repository import ParameterRepository
from src.schemas.ho import DocParameterValueWrite, DocumentCreate, DocumentUpdate


class DocumentService:
    def __init__(
        self,
        repo: DocumentRepository,
        param_value_repo: DocParameterValueRepository,
        doc_class_param_repo: DocClassParameterRepository,
        param_repo: ParameterRepository,
        enum_value_repo: EnumValueRepository,
    ) -> None:
        self.repo = repo
        self.param_value_repo = param_value_repo
        self.doc_class_param_repo = doc_class_param_repo
        self.param_repo = param_repo
        self.enum_value_repo = enum_value_repo

    def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Document]:
        return self.repo.get_all(skip=skip, limit=limit)

    def get_by_id(self, doc_id: int) -> Document:
        obj = self.repo.get_by_id(doc_id)
        if not obj:
            raise NotFoundError("Document not found")
        return obj

    def get_by_ho(self, ho_id: int) -> Sequence[Document]:
        return self.repo.get_by_ho(ho_id)

    def create(self, data: DocumentCreate) -> Document:
        """Создаёт документ и заготовки значений параметров для его типа."""
        doc = self.repo.create(data.model_dump())
        class_params = self.doc_class_param_repo.get_by_doc_type(data.doc_type_id)
        for cp in class_params:
            self.param_value_repo.create({"document_id": doc.id, "doc_class_param_id": cp.id})
        return doc

    def update(self, doc_id: int, data: DocumentUpdate) -> Document:
        obj = self.get_by_id(doc_id)
        return self.repo.update(obj, data.model_dump(exclude_none=True))

    def delete(self, doc_id: int) -> None:
        obj = self.get_by_id(doc_id)
        self.repo.delete(obj)

    def get_parameter_values(self, doc_id: int) -> Sequence[DocParameterValue]:
        self.get_by_id(doc_id)
        return self.param_value_repo.get_by_document(doc_id)

    def write_parameter_value(
        self, doc_id: int, doc_class_param_id: int, data: DocParameterValueWrite
    ) -> DocParameterValue:
        """Записывает значение параметра документа с валидацией типа."""
        self.get_by_id(doc_id)

        cp = self.doc_class_param_repo.get_by_id(doc_class_param_id)
        if not cp:
            raise NotFoundError("DocClassParameter not found")
        param = self.param_repo.get_by_id(cp.parameter_id)
        if not param:
            raise NotFoundError("Parameter not found")
        param_type_ev = self.enum_value_repo.get_by_id(param.param_type_id)
        param_type_code = param_type_ev.code if param_type_ev else None

        if param_type_code == "number":
            val = data.value_real if data.value_real is not None else data.value_int
            if val is not None:
                if cp.min_value is not None and val < cp.min_value:
                    raise BusinessRuleError(f"Value below minimum {cp.min_value}")
                if cp.max_value is not None and val > cp.max_value:
                    raise BusinessRuleError(f"Value above maximum {cp.max_value}")
        elif param_type_code == "enum" and data.value_enum_id is not None:
            ev = self.enum_value_repo.get_by_id(data.value_enum_id)
            if not ev or ev.enum_type_id != param.enum_type_id:
                raise BusinessRuleError("Invalid enum value for this parameter")
        existing = self.param_value_repo.get_by_doc_and_class_param(doc_id, doc_class_param_id)
        update_data = data.model_dump()
        update_data.update({"document_id": doc_id, "doc_class_param_id": doc_class_param_id})

        if existing:
            return self.param_value_repo.update(existing, data.model_dump())
        return self.param_value_repo.create(update_data)
