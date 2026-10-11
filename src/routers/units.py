from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.database.database import get_session
from src.repository.unit_repository import UnitSimpleRepository
from src.schemas.units import UnitSimpleCreate, UnitSimpleRead, UnitSimpleUpdate
from src.services.unit_service import UnitSimpleService

router = APIRouter()


def get_service(session: Session = Depends(get_session)) -> UnitSimpleService:
    return UnitSimpleService(UnitSimpleRepository(session))


@router.get("/", response_model=List[UnitSimpleRead])
def list_units(skip: int = 0, limit: int = 100, service: UnitSimpleService = Depends(get_service)):
    return service.get_all(skip=skip, limit=limit)


@router.post("/", response_model=UnitSimpleRead, status_code=201)
def create_unit(data: UnitSimpleCreate, service: UnitSimpleService = Depends(get_service)):
    return service.create(data)


@router.get("/{unit_id}", response_model=UnitSimpleRead)
def get_unit(unit_id: int, service: UnitSimpleService = Depends(get_service)):
    return service.get_by_id(unit_id)


@router.put("/{unit_id}", response_model=UnitSimpleRead)
def update_unit(unit_id: int, data: UnitSimpleUpdate, service: UnitSimpleService = Depends(get_service)):
    return service.update(unit_id, data)


@router.delete("/{unit_id}", status_code=204)
def delete_unit(unit_id: int, service: UnitSimpleService = Depends(get_service)):
    service.delete(unit_id)
