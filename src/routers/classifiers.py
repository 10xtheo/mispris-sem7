from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.database.database import get_session
from src.repository.classifier_repository import (
    DocumentClassifierRepository,
    HoClassifierRepository,
    ItemClassifierRepository,
    SxdClassifierRepository,
)
from src.schemas.classifiers import (
    DocumentClassifierCreate,
    DocumentClassifierRead,
    DocumentClassifierUpdate,
    HoClassifierCreate,
    HoClassifierRead,
    HoClassifierTree,
    HoClassifierUpdate,
    ItemClassifierCreate,
    ItemClassifierRead,
    ItemClassifierUpdate,
    SxdClassifierCreate,
    SxdClassifierRead,
    SxdClassifierUpdate,
)
from src.services.classifier_service import (
    DocumentClassifierService,
    HoClassifierService,
    ItemClassifierService,
    SxdClassifierService,
)

router = APIRouter()


def get_sxd_clf_service(session: Session = Depends(get_session)) -> SxdClassifierService:
    return SxdClassifierService(SxdClassifierRepository(session))


def get_ho_clf_service(session: Session = Depends(get_session)) -> HoClassifierService:
    return HoClassifierService(HoClassifierRepository(session))


def get_doc_clf_service(session: Session = Depends(get_session)) -> DocumentClassifierService:
    return DocumentClassifierService(DocumentClassifierRepository(session))


def get_item_clf_service(session: Session = Depends(get_session)) -> ItemClassifierService:
    return ItemClassifierService(ItemClassifierRepository(session))


# --- SxdClassifier ---

@router.get("/sxd", response_model=List[SxdClassifierRead])
def list_sxd_classifiers(skip: int = 0, limit: int = 100, service=Depends(get_sxd_clf_service)):
    return service.get_all(skip=skip, limit=limit)


@router.post("/sxd", response_model=SxdClassifierRead, status_code=201)
def create_sxd_classifier(data: SxdClassifierCreate, service=Depends(get_sxd_clf_service)):
    return service.create(data)


@router.get("/sxd/{clf_id}", response_model=SxdClassifierRead)
def get_sxd_classifier(clf_id: int, service=Depends(get_sxd_clf_service)):
    return service.get_by_id(clf_id)


@router.put("/sxd/{clf_id}", response_model=SxdClassifierRead)
def update_sxd_classifier(clf_id: int, data: SxdClassifierUpdate, service=Depends(get_sxd_clf_service)):
    return service.update(clf_id, data)


@router.delete("/sxd/{clf_id}", status_code=204)
def delete_sxd_classifier(clf_id: int, service=Depends(get_sxd_clf_service)):
    service.delete(clf_id)


# --- HoClassifier ---

@router.get("/ho", response_model=List[HoClassifierRead])
def list_ho_classifiers(skip: int = 0, limit: int = 100, service=Depends(get_ho_clf_service)):
    return service.get_all(skip=skip, limit=limit)


@router.get("/ho/tree", response_model=List[HoClassifierTree])
def get_ho_classifier_tree(service=Depends(get_ho_clf_service)):
    """Возвращает классификатор ХО в виде дерева."""
    return service.get_tree()


@router.post("/ho", response_model=HoClassifierRead, status_code=201)
def create_ho_classifier(data: HoClassifierCreate, service=Depends(get_ho_clf_service)):
    return service.create(data)


@router.get("/ho/{clf_id}", response_model=HoClassifierRead)
def get_ho_classifier(clf_id: int, service=Depends(get_ho_clf_service)):
    return service.get_by_id(clf_id)


@router.put("/ho/{clf_id}", response_model=HoClassifierRead)
def update_ho_classifier(clf_id: int, data: HoClassifierUpdate, service=Depends(get_ho_clf_service)):
    return service.update(clf_id, data)


@router.delete("/ho/{clf_id}", status_code=204)
def delete_ho_classifier(clf_id: int, service=Depends(get_ho_clf_service)):
    service.delete(clf_id)


# --- DocumentClassifier ---

@router.get("/documents", response_model=List[DocumentClassifierRead])
def list_doc_classifiers(skip: int = 0, limit: int = 100, service=Depends(get_doc_clf_service)):
    return service.get_all(skip=skip, limit=limit)


@router.post("/documents", response_model=DocumentClassifierRead, status_code=201)
def create_doc_classifier(data: DocumentClassifierCreate, service=Depends(get_doc_clf_service)):
    return service.create(data)


@router.get("/documents/{clf_id}", response_model=DocumentClassifierRead)
def get_doc_classifier(clf_id: int, service=Depends(get_doc_clf_service)):
    return service.get_by_id(clf_id)


@router.put("/documents/{clf_id}", response_model=DocumentClassifierRead)
def update_doc_classifier(clf_id: int, data: DocumentClassifierUpdate, service=Depends(get_doc_clf_service)):
    return service.update(clf_id, data)


@router.delete("/documents/{clf_id}", status_code=204)
def delete_doc_classifier(clf_id: int, service=Depends(get_doc_clf_service)):
    service.delete(clf_id)


# --- ItemClassifier ---

@router.get("/items", response_model=List[ItemClassifierRead])
def list_item_classifiers(skip: int = 0, limit: int = 100, service=Depends(get_item_clf_service)):
    return service.get_all(skip=skip, limit=limit)


@router.post("/items", response_model=ItemClassifierRead, status_code=201)
def create_item_classifier(data: ItemClassifierCreate, service=Depends(get_item_clf_service)):
    return service.create(data)


@router.get("/items/{clf_id}", response_model=ItemClassifierRead)
def get_item_classifier(clf_id: int, service=Depends(get_item_clf_service)):
    return service.get_by_id(clf_id)


@router.put("/items/{clf_id}", response_model=ItemClassifierRead)
def update_item_classifier(clf_id: int, data: ItemClassifierUpdate, service=Depends(get_item_clf_service)):
    return service.update(clf_id, data)


@router.delete("/items/{clf_id}", status_code=204)
def delete_item_classifier(clf_id: int, service=Depends(get_item_clf_service)):
    service.delete(clf_id)
