from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.database.database import get_session
from src.repository.role_repository import AvailableRolesRepository, SxdRoleRepository
from src.schemas.roles import (
    AvailableRoleCreate,
    AvailableRoleRead,
    AvailableRoleUpdate,
    SxdRoleCreate,
    SxdRoleRead,
    SxdRoleUpdate,
)
from src.services.role_service import AvailableRolesService, SxdRoleService

router = APIRouter()


def get_role_service(session: Session = Depends(get_session)) -> SxdRoleService:
    return SxdRoleService(SxdRoleRepository(session))


def get_avail_service(session: Session = Depends(get_session)) -> AvailableRolesService:
    return AvailableRolesService(AvailableRolesRepository(session))


@router.get("/", response_model=List[SxdRoleRead])
def list_roles(skip: int = 0, limit: int = 100, service: SxdRoleService = Depends(get_role_service)):
    return service.get_all(skip=skip, limit=limit)


@router.post("/", response_model=SxdRoleRead, status_code=201)
def create_role(data: SxdRoleCreate, service: SxdRoleService = Depends(get_role_service)):
    return service.create(data)


@router.get("/{role_id}", response_model=SxdRoleRead)
def get_role(role_id: int, service: SxdRoleService = Depends(get_role_service)):
    return service.get_by_id(role_id)


@router.put("/{role_id}", response_model=SxdRoleRead)
def update_role(role_id: int, data: SxdRoleUpdate, service: SxdRoleService = Depends(get_role_service)):
    return service.update(role_id, data)


@router.delete("/{role_id}", status_code=204)
def delete_role(role_id: int, service: SxdRoleService = Depends(get_role_service)):
    service.delete(role_id)


@router.get("/available/by-ho-type/{ho_type_id}", response_model=List[AvailableRoleRead])
def list_available_roles(ho_type_id: int, service: AvailableRolesService = Depends(get_avail_service)):
    return service.get_by_ho_type(ho_type_id)


@router.post("/available", response_model=AvailableRoleRead, status_code=201)
def create_available_role(data: AvailableRoleCreate, service: AvailableRolesService = Depends(get_avail_service)):
    return service.create(data)


@router.put("/available/{avail_id}", response_model=AvailableRoleRead)
def update_available_role(avail_id: int, data: AvailableRoleUpdate, service: AvailableRolesService = Depends(get_avail_service)):
    return service.update(avail_id, data)


@router.delete("/available/{avail_id}", status_code=204)
def delete_available_role(avail_id: int, service: AvailableRolesService = Depends(get_avail_service)):
    service.delete(avail_id)
