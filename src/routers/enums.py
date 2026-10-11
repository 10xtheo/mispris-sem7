from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.database.database import get_session
from src.repository.enum_repository import EnumTypeRepository, EnumValueRepository
from src.schemas.enums import (
    EnumTypeCreate,
    EnumTypeRead,
    EnumTypeUpdate,
    EnumValueCreate,
    EnumValueRead,
    EnumValueUpdate,
)
from src.services.enum_service import EnumTypeService, EnumValueService

router = APIRouter()


def get_enum_type_service(session: Session = Depends(get_session)) -> EnumTypeService:
    return EnumTypeService(EnumTypeRepository(session))


def get_enum_value_service(session: Session = Depends(get_session)) -> EnumValueService:
    return EnumValueService(EnumValueRepository(session))


@router.get("/types", response_model=List[EnumTypeRead])
def list_enum_types(skip: int = 0, limit: int = 100, service: EnumTypeService = Depends(get_enum_type_service)):
    return service.get_all(skip=skip, limit=limit)


@router.post("/types", response_model=EnumTypeRead, status_code=201)
def create_enum_type(data: EnumTypeCreate, service: EnumTypeService = Depends(get_enum_type_service)):
    return service.create(data)


@router.get("/types/{type_id}", response_model=EnumTypeRead)
def get_enum_type(type_id: int, service: EnumTypeService = Depends(get_enum_type_service)):
    return service.get_by_id(type_id)


@router.put("/types/{type_id}", response_model=EnumTypeRead)
def update_enum_type(type_id: int, data: EnumTypeUpdate, service: EnumTypeService = Depends(get_enum_type_service)):
    return service.update(type_id, data)


@router.delete("/types/{type_id}", status_code=204)
def delete_enum_type(type_id: int, service: EnumTypeService = Depends(get_enum_type_service)):
    service.delete(type_id)


@router.get("/values", response_model=List[EnumValueRead])
def list_enum_values(skip: int = 0, limit: int = 100, service: EnumValueService = Depends(get_enum_value_service)):
    return service.get_all(skip=skip, limit=limit)


@router.get("/values/by-type/{enum_type_id}", response_model=List[EnumValueRead])
def list_values_by_type(enum_type_id: int, service: EnumValueService = Depends(get_enum_value_service)):
    return service.get_by_type(enum_type_id)


@router.post("/values", response_model=EnumValueRead, status_code=201)
def create_enum_value(data: EnumValueCreate, service: EnumValueService = Depends(get_enum_value_service)):
    return service.create(data)


@router.get("/values/{value_id}", response_model=EnumValueRead)
def get_enum_value(value_id: int, service: EnumValueService = Depends(get_enum_value_service)):
    return service.get_by_id(value_id)


@router.put("/values/{value_id}", response_model=EnumValueRead)
def update_enum_value(value_id: int, data: EnumValueUpdate, service: EnumValueService = Depends(get_enum_value_service)):
    return service.update(value_id, data)


@router.delete("/values/{value_id}", status_code=204)
def delete_enum_value(value_id: int, service: EnumValueService = Depends(get_enum_value_service)):
    service.delete(value_id)
