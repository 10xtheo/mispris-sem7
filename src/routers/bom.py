from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from src.database.database import get_session
from src.repository.bom_repository import ItemBomRepository, ItemChangeRepository, ModificationRepository
from src.repository.classifier_repository import ItemClassifierRepository
from src.repository.enum_repository import EnumValueRepository
from src.repository.item_repository import ItemRepository, UnitQuantityRepository
from src.schemas.bom import (
    BomComponentAdd,
    BomComponentReplace,
    BomComponentUpdate,
    BomRowRead,
    BomSpecRead,
    BomTreeRead,
    ChangeRead,
    ModificationCreate,
    NormsRead,
)
from src.schemas.items import ItemRead
from src.services.bom_service import BomService

router = APIRouter()

AT_QUERY = Query(default=None, description="Момент времени (ISO 8601), на который показать состав; по умолчанию — сейчас")


def get_bom_service(session: Session = Depends(get_session)) -> BomService:
    return BomService(
        items=ItemRepository(session),
        boms=ItemBomRepository(session),
        changes=ItemChangeRepository(session),
        modifications=ModificationRepository(session),
        enum_values=EnumValueRepository(session),
        units=UnitQuantityRepository(session),
        classifiers=ItemClassifierRepository(session),
    )


@router.get("/{item_id}/bom", response_model=BomSpecRead)
def get_spec(item_id: int, at: Optional[datetime] = AT_QUERY, service: BomService = Depends(get_bom_service)):
    return service.get_spec(item_id, at)


@router.get("/{item_id}/bom/tree", response_model=BomTreeRead)
def find_bom(item_id: int, at: Optional[datetime] = AT_QUERY, service: BomService = Depends(get_bom_service)):
    return service.find_bom(item_id, at)


@router.get("/{item_id}/bom/norms", response_model=NormsRead)
def calc_bom(
    item_id: int,
    quantity: Decimal = Query(default=Decimal("1"), gt=0, description="Количество изделий"),
    class_id: Optional[int] = Query(default=None, description="Класс материалов (с подклассами)"),
    at: Optional[datetime] = AT_QUERY,
    service: BomService = Depends(get_bom_service),
):
    return service.calc_bom(item_id, quantity, class_id, at)


@router.post("/{item_id}/bom", response_model=BomRowRead, status_code=201)
def add_component(item_id: int, data: BomComponentAdd, service: BomService = Depends(get_bom_service)):
    return service.add_component(item_id, data)


@router.put("/{item_id}/bom/{component_id}", response_model=BomRowRead)
def update_component(
    item_id: int, component_id: int, data: BomComponentUpdate, service: BomService = Depends(get_bom_service)
):
    return service.update_component(item_id, component_id, data)


@router.post(
    "/{item_id}/bom/{component_id}/replace", response_model=BomRowRead
)
def replace_component(
    item_id: int, component_id: int, data: BomComponentReplace, service: BomService = Depends(get_bom_service)
):
    return service.replace_component(item_id, component_id, data)


@router.delete("/{item_id}/bom/{component_id}", status_code=204)
def remove_component(
    item_id: int,
    component_id: int,
    reason: Optional[str] = Query(default=None, max_length=500),
    service: BomService = Depends(get_bom_service),
):
    service.remove_component(item_id, component_id, reason)


@router.get("/{item_id}/bom/changes", response_model=List[ChangeRead])
def history(item_id: int, service: BomService = Depends(get_bom_service)):
    return service.history(item_id)


@router.post(
    "/{item_id}/modifications", response_model=ItemRead, status_code=201
)
def create_modification(item_id: int, data: ModificationCreate, service: BomService = Depends(get_bom_service)):
    return service.create_modification(item_id, data)


@router.get("/{item_id}/modifications", response_model=List[ItemRead])
def list_modifications(item_id: int, service: BomService = Depends(get_bom_service)):
    return service.get_modifications(item_id)
