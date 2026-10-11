from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from src.database.database import get_session
from src.repository.sxd_repository import SxdRepository
from src.schemas.sxd import SxdCreate, SxdRead, SxdUpdate
from src.services.sxd_service import SxdService

router = APIRouter()


def get_service(session: Session = Depends(get_session)) -> SxdService:
    return SxdService(SxdRepository(session))


@router.get("/", response_model=List[SxdRead])
def list_sxd(
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = Query(default=None, description="Фильтр по имени"),
    service: SxdService = Depends(get_service),
):
    if name:
        return service.search(name)
    return service.get_all(skip=skip, limit=limit)


@router.post("/", response_model=SxdRead, status_code=201)
def create_sxd(data: SxdCreate, service: SxdService = Depends(get_service)):
    return service.create(data)


@router.get("/{sxd_id}", response_model=SxdRead)
def get_sxd(sxd_id: int, service: SxdService = Depends(get_service)):
    return service.get_by_id(sxd_id)


@router.put("/{sxd_id}", response_model=SxdRead)
def update_sxd(sxd_id: int, data: SxdUpdate, service: SxdService = Depends(get_service)):
    return service.update(sxd_id, data)


@router.delete("/{sxd_id}", status_code=204)
def delete_sxd(sxd_id: int, service: SxdService = Depends(get_service)):
    service.delete(sxd_id)
