from typing import List, cast

from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.database.database import get_session
from src.repository.document_repository import DocParameterValueRepository, DocumentRepository
from src.repository.enum_repository import EnumValueRepository
from src.repository.ho_repository import DocClassParameterRepository
from src.repository.parameter_repository import ParameterRepository
from src.schemas.ho import (
    DocParameterValueRead,
    DocParameterValueWrite,
    DocumentCreate,
    DocumentRead,
    DocumentUpdate,
)
from src.services.document_service import DocumentService

router = APIRouter()


def get_service(session: Session = Depends(get_session)) -> DocumentService:
    return DocumentService(
        repo=DocumentRepository(session),
        param_value_repo=DocParameterValueRepository(session),
        doc_class_param_repo=DocClassParameterRepository(session),
        param_repo=ParameterRepository(session),
        enum_value_repo=EnumValueRepository(session),
    )


@router.get("/", response_model=List[DocumentRead])
def list_documents(skip: int = 0, limit: int = 100, service: DocumentService = Depends(get_service)):
    return service.get_all(skip=skip, limit=limit)


@router.post("/", response_model=DocumentRead, status_code=201)
def create_document(data: DocumentCreate, service: DocumentService = Depends(get_service)):
    return service.create(data)


@router.get("/{doc_id}", response_model=DocumentRead)
def get_document(doc_id: int, service: DocumentService = Depends(get_service)):
    return service.get_by_id(doc_id)


@router.put("/{doc_id}", response_model=DocumentRead)
def update_document(doc_id: int, data: DocumentUpdate, service: DocumentService = Depends(get_service)):
    return service.update(doc_id, data)


@router.delete("/{doc_id}", status_code=204)
def delete_document(doc_id: int, service: DocumentService = Depends(get_service)):
    service.delete(doc_id)


@router.get("/{doc_id}/parameters", response_model=List[DocParameterValueRead])
def get_doc_parameters(doc_id: int, service: DocumentService = Depends(get_service)):
    result = service.get_parameter_values(doc_id)
    return [
        DocParameterValueRead(
            id=cast(int, r.id), document_id=r.document_id, doc_class_param_id=r.doc_class_param_id,
            value_str=r.value_str, value_int=r.value_int, value_real=r.value_real,
            value_dt=r.value_dt, value_enum_id=r.value_enum_id,
        )
        for r in result
    ]


@router.put("/{doc_id}/parameters/{doc_class_param_id}", response_model=DocParameterValueRead)
def write_doc_parameter(
    doc_id: int,
    doc_class_param_id: int,
    data: DocParameterValueWrite,
    service: DocumentService = Depends(get_service),
):
    result = service.write_parameter_value(doc_id, doc_class_param_id, data)
    return DocParameterValueRead(
        id=cast(int, result.id), document_id=result.document_id, doc_class_param_id=result.doc_class_param_id,
        value_str=result.value_str, value_int=result.value_int, value_real=result.value_real,
        value_dt=result.value_dt, value_enum_id=result.value_enum_id,
    )
