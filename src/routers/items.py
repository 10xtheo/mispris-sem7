from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from src.database.database import get_session
from src.repository.bom_repository import ItemBomRepository
from src.repository.enum_repository import EnumTypeRepository, EnumValueRepository
from src.repository.item_repository import ItemBatchRepository, ItemRepository, UnitQuantityRepository
from src.schemas.items import (
    ItemBatchCreate,
    ItemBatchRead,
    ItemCreate,
    ItemRead,
    ItemUpdate,
    UnitQuantityCreate,
    UnitQuantityRead,
)
from src.services.item_service import ItemBatchService, ItemService, UnitQuantityService

router = APIRouter()


def get_item_service(session: Session = Depends(get_session)) -> ItemService:
    return ItemService(
        ItemRepository(session),
        enum_values=EnumValueRepository(session),
        enum_types=EnumTypeRepository(session),
        boms=ItemBomRepository(session),
    )


def get_uq_service(session: Session = Depends(get_session)) -> UnitQuantityService:
    return UnitQuantityService(UnitQuantityRepository(session))


def get_batch_service(session: Session = Depends(get_session)) -> ItemBatchService:
    return ItemBatchService(ItemBatchRepository(session))


@router.get("/", response_model=List[ItemRead])
def list_items(
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = Query(default=None),
    service: ItemService = Depends(get_item_service),
):
    if name:
        return service.search(name)
    return service.get_all(skip=skip, limit=limit)


@router.post("/", response_model=ItemRead, status_code=201)
def create_item(data: ItemCreate, service: ItemService = Depends(get_item_service)):
    return service.create(data)


@router.get("/{item_id}", response_model=ItemRead)
def get_item(item_id: int, service: ItemService = Depends(get_item_service)):
    return service.get_by_id(item_id)


@router.put("/{item_id}", response_model=ItemRead)
def update_item(item_id: int, data: ItemUpdate, service: ItemService = Depends(get_item_service)):
    return service.update(item_id, data)


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: int, service: ItemService = Depends(get_item_service)):
    service.delete(item_id)


@router.get("/{item_id}/units", response_model=List[UnitQuantityRead])
def get_item_units(item_id: int, service: UnitQuantityService = Depends(get_uq_service)):
    return service.get_by_item(item_id)


@router.post("/units", response_model=UnitQuantityRead, status_code=201)
def add_item_unit(data: UnitQuantityCreate, service: UnitQuantityService = Depends(get_uq_service)):
    return service.create(data)


@router.delete("/units/{uq_id}", status_code=204)
def remove_item_unit(uq_id: int, service: UnitQuantityService = Depends(get_uq_service)):
    service.delete(uq_id)


@router.get("/{item_id}/batches", response_model=List[ItemBatchRead])
def get_item_batches(item_id: int, service: ItemBatchService = Depends(get_batch_service)):
    return service.get_by_item(item_id)


@router.post("/batches", response_model=ItemBatchRead, status_code=201)
def create_batch(data: ItemBatchCreate, service: ItemBatchService = Depends(get_batch_service)):
    return service.create(data)


@router.delete("/batches/{batch_id}", status_code=204)
def delete_batch(batch_id: int, service: ItemBatchService = Depends(get_batch_service)):
    service.delete(batch_id)
