from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.database.database import get_session
from src.repository.ho_repository import PositionListRepository
from src.repository.position_repository import HoPositionRepository, PricelistRepository, PricelistSetRepository
from src.schemas.positions import (
    HoPositionCreate,
    HoPositionRead,
    HoPositionUpdate,
    PricelistCreate,
    PricelistRead,
    PricelistSetCreate,
    PricelistSetRead,
)
from src.services.position_service import HoPositionService, PricelistService, PricelistSetService

router = APIRouter()


def get_pos_service(session: Session = Depends(get_session)) -> HoPositionService:
    return HoPositionService(
        position_repo=HoPositionRepository(session),
        position_list_repo=PositionListRepository(session),
    )


def get_pricelist_service(session: Session = Depends(get_session)) -> PricelistService:
    return PricelistService(PricelistRepository(session))


def get_pricelist_set_service(session: Session = Depends(get_session)) -> PricelistSetService:
    return PricelistSetService(PricelistSetRepository(session))


@router.get("/ho/{ho_id}", response_model=List[HoPositionRead])
def get_ho_positions(ho_id: int, service: HoPositionService = Depends(get_pos_service)):
    return service.get_by_ho(ho_id)


@router.post("/ho/{ho_id}", response_model=HoPositionRead, status_code=201)
def add_ho_position(ho_id: int, data: HoPositionCreate, service: HoPositionService = Depends(get_pos_service)):
    """ADD_HO_POSITION: добавляет строку. total_amount вычисляется автоматически."""
    return service.add_position(ho_id, data)


@router.put("/{pos_id}", response_model=HoPositionRead)
def update_position(pos_id: int, data: HoPositionUpdate, service: HoPositionService = Depends(get_pos_service)):
    return service.update_position(pos_id, data)


@router.delete("/{pos_id}", status_code=204)
def delete_position(pos_id: int, service: HoPositionService = Depends(get_pos_service)):
    service.delete_position(pos_id)


@router.get("/pricelist-sets", response_model=List[PricelistSetRead])
def list_pricelist_sets(skip: int = 0, limit: int = 100, service=Depends(get_pricelist_set_service)):
    return service.get_all(skip=skip, limit=limit)


@router.post("/pricelist-sets", response_model=PricelistSetRead, status_code=201)
def create_pricelist_set(data: PricelistSetCreate, service=Depends(get_pricelist_set_service)):
    return service.create(data)


@router.get("/pricelists/by-set/{set_id}", response_model=List[PricelistRead])
def get_pricelists(set_id: int, service=Depends(get_pricelist_service)):
    return service.get_by_set(set_id)


@router.post("/pricelists", response_model=PricelistRead, status_code=201)
def create_pricelist(data: PricelistCreate, service=Depends(get_pricelist_service)):
    return service.create(data)


@router.delete("/pricelists/{pl_id}", status_code=204)
def delete_pricelist(pl_id: int, service=Depends(get_pricelist_service)):
    service.delete(pl_id)
