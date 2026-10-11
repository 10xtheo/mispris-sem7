from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.database.database import get_session
from src.repository.parameter_repository import ParameterRepository
from src.schemas.parameters import ParameterCreate, ParameterRead, ParameterUpdate
from src.services.parameter_service import ParameterService

router = APIRouter()


def get_service(session: Session = Depends(get_session)) -> ParameterService:
    return ParameterService(ParameterRepository(session))


@router.get("/", response_model=List[ParameterRead])
def list_parameters(skip: int = 0, limit: int = 100, service: ParameterService = Depends(get_service)):
    return service.get_all(skip=skip, limit=limit)


@router.post("/", response_model=ParameterRead, status_code=201)
def create_parameter(data: ParameterCreate, service: ParameterService = Depends(get_service)):
    return service.create(data)


@router.get("/{param_id}", response_model=ParameterRead)
def get_parameter(param_id: int, service: ParameterService = Depends(get_service)):
    return service.get_by_id(param_id)


@router.put("/{param_id}", response_model=ParameterRead)
def update_parameter(param_id: int, data: ParameterUpdate, service: ParameterService = Depends(get_service)):
    return service.update(param_id, data)


@router.delete("/{param_id}", status_code=204)
def delete_parameter(param_id: int, service: ParameterService = Depends(get_service)):
    service.delete(param_id)
