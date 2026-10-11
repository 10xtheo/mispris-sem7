from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.database.database import get_session
from src.repository.packaging_repository import (
    PackagingNormRepository,
    PackagingRepository,
    PackagingTypeRepository,
)
from src.schemas.packaging import (
    PackagingCreate,
    PackagingNormCreate,
    PackagingNormRead,
    PackagingRead,
    PackagingTypeCreate,
    PackagingTypeRead,
    PackagingTypeUpdate,
    PackagingUpdate,
)
from src.services.packaging_service import PackagingNormService, PackagingService, PackagingTypeService

router = APIRouter()


def get_type_service(session: Session = Depends(get_session)) -> PackagingTypeService:
    return PackagingTypeService(PackagingTypeRepository(session))


def get_pkg_service(session: Session = Depends(get_session)) -> PackagingService:
    return PackagingService(PackagingRepository(session))


def get_norm_service(session: Session = Depends(get_session)) -> PackagingNormService:
    return PackagingNormService(PackagingNormRepository(session))


@router.get("/types", response_model=List[PackagingTypeRead])
def list_packaging_types(skip: int = 0, limit: int = 100, service=Depends(get_type_service)):
    return service.get_all(skip=skip, limit=limit)


@router.post("/types", response_model=PackagingTypeRead, status_code=201)
def create_packaging_type(data: PackagingTypeCreate, service=Depends(get_type_service)):
    return service.create(data)


@router.put("/types/{type_id}", response_model=PackagingTypeRead)
def update_packaging_type(type_id: int, data: PackagingTypeUpdate, service=Depends(get_type_service)):
    return service.update(type_id, data)


@router.delete("/types/{type_id}", status_code=204)
def delete_packaging_type(type_id: int, service=Depends(get_type_service)):
    service.delete(type_id)


@router.get("/", response_model=List[PackagingRead])
def list_packagings(skip: int = 0, limit: int = 100, service=Depends(get_pkg_service)):
    return service.get_all(skip=skip, limit=limit)


@router.post("/", response_model=PackagingRead, status_code=201)
def create_packaging(data: PackagingCreate, service=Depends(get_pkg_service)):
    return service.create(data)


@router.put("/{pkg_id}", response_model=PackagingRead)
def update_packaging(pkg_id: int, data: PackagingUpdate, service=Depends(get_pkg_service)):
    return service.update(pkg_id, data)


@router.delete("/{pkg_id}", status_code=204)
def delete_packaging(pkg_id: int, service=Depends(get_pkg_service)):
    service.delete(pkg_id)


@router.get("/norms/by-item/{item_id}", response_model=List[PackagingNormRead])
def get_norms_by_item(item_id: int, service=Depends(get_norm_service)):
    return service.get_by_item(item_id)


@router.post("/norms", response_model=PackagingNormRead, status_code=201)
def create_norm(data: PackagingNormCreate, service=Depends(get_norm_service)):
    return service.create(data)


@router.delete("/norms/{norm_id}", status_code=204)
def delete_norm(norm_id: int, service=Depends(get_norm_service)):
    service.delete(norm_id)
