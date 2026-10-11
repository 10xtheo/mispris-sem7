from datetime import date as dt
from typing import List, Optional, cast

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from src.database.database import get_session
from src.repository.enum_repository import EnumValueRepository
from src.repository.ho_repository import (
    HoClassParameterRepository,
    HoParameterValueRepository,
    HoRepository,
    PositionListRepository,
    SxdRoleInHoRepository,
)
from src.repository.parameter_repository import ParameterRepository
from src.repository.role_repository import AvailableRolesRepository
from src.schemas.ho import (
    HoClassParameterCreate,
    HoClassParameterRead,
    HoCreate,
    HoParameterValueRead,
    HoParameterValueWrite,
    HoRead,
    HoReadFull,
    HoSearchParams,
    HoUpdate,
    SxdRoleInHoCreate,
    SxdRoleInHoRead,
)
from src.services.ho_service import HoClassParameterService, HoService

router = APIRouter()


def get_ho_service(session: Session = Depends(get_session)) -> HoService:
    return HoService(
        ho_repo=HoRepository(session),
        ho_class_param_repo=HoClassParameterRepository(session),
        ho_param_value_repo=HoParameterValueRepository(session),
        role_in_ho_repo=SxdRoleInHoRepository(session),
        available_roles_repo=AvailableRolesRepository(session),
        position_list_repo=PositionListRepository(session),
        param_repo=ParameterRepository(session),
        enum_value_repo=EnumValueRepository(session),
    )


def get_ho_class_param_service(session: Session = Depends(get_session)) -> HoClassParameterService:
    return HoClassParameterService(HoClassParameterRepository(session))


@router.get("/", response_model=List[HoRead])
def list_ho(
    ho_type_id: Optional[int] = Query(default=None),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    document_number: Optional[str] = Query(default=None),
    skip: int = 0,
    limit: int = 100,
    service: HoService = Depends(get_ho_service),
):
    """Поиск ХО по классу, дате и другим параметрам (FIND_HO_BY_CLASS)."""
    params = HoSearchParams(
        ho_type_id=ho_type_id,
        date_from=dt.fromisoformat(date_from) if date_from else None,
        date_to=dt.fromisoformat(date_to) if date_to else None,
        document_number=document_number,
        skip=skip,
        limit=limit,
    )
    return service.search(params)


@router.post("/", response_model=HoRead, status_code=201)
def create_ho(data: HoCreate, service: HoService = Depends(get_ho_service)):
    """Создаёт ХО и автоматически инициализирует параметры (INS_HO)."""
    return service.create(data)


@router.get("/{ho_id}", response_model=HoRead)
def get_ho(ho_id: int, service: HoService = Depends(get_ho_service)):
    return service.get_by_id(ho_id)


@router.get("/{ho_id}/full", response_model=HoReadFull)
def get_ho_full(ho_id: int, service: HoService = Depends(get_ho_service)):
    """Полное представление ХО: параметры + роли (PRESENT_HO)."""
    return service.get_full(ho_id)


@router.put("/{ho_id}", response_model=HoRead)
def update_ho(ho_id: int, data: HoUpdate, service: HoService = Depends(get_ho_service)):
    return service.update(ho_id, data)


@router.delete("/{ho_id}", status_code=204)
def delete_ho(ho_id: int, service: HoService = Depends(get_ho_service)):
    service.delete(ho_id)


@router.get("/{ho_id}/parameters", response_model=List[HoParameterValueRead])
def get_ho_parameters(ho_id: int, service: HoService = Depends(get_ho_service)):
    return service.get_parameter_values(ho_id)


@router.put("/{ho_id}/parameters/{ho_class_param_id}", response_model=HoParameterValueRead)
def write_ho_parameter(
    ho_id: int,
    ho_class_param_id: int,
    data: HoParameterValueWrite,
    service: HoService = Depends(get_ho_service),
):
    """Записывает значение параметра ХО с валидацией (WRITE_HO_PAR)."""
    result = service.write_parameter_value(ho_id, ho_class_param_id, data)
    return HoParameterValueRead(
        id=cast(int, result.id),
        ho_id=result.ho_id,
        ho_class_param_id=result.ho_class_param_id,
        value_str=result.value_str,
        value_int=result.value_int,
        value_real=result.value_real,
        value_dt=result.value_dt,
        value_enum_id=result.value_enum_id,
    )


@router.get("/{ho_id}/roles", response_model=List[SxdRoleInHoRead])
def get_ho_roles(ho_id: int, service: HoService = Depends(get_ho_service)):
    return service.get_roles(ho_id)


@router.post("/{ho_id}/roles", response_model=SxdRoleInHoRead, status_code=201)
def assign_role(ho_id: int, data: SxdRoleInHoCreate, service: HoService = Depends(get_ho_service)):
    """Назначает СХД на роль в ХО (SET_HO_ACTOR)."""
    result = service.assign_role(ho_id, data)
    return SxdRoleInHoRead(id=cast(int, result.id), ho_id=result.ho_id, sxd_id=result.sxd_id, role_id=result.role_id)


@router.delete("/{ho_id}/roles/{role_id}/sxd/{sxd_id}", status_code=204)
def remove_role(ho_id: int, role_id: int, sxd_id: int, service: HoService = Depends(get_ho_service)):
    service.remove_role(ho_id, sxd_id, role_id)


@router.get("/class-parameters/by-type/{ho_type_id}", response_model=List[HoClassParameterRead])
def list_class_params(ho_type_id: int, service: HoClassParameterService = Depends(get_ho_class_param_service)):
    return service.get_by_ho_type(ho_type_id)


@router.post("/class-parameters", response_model=HoClassParameterRead, status_code=201)
def create_class_param(data: HoClassParameterCreate, service: HoClassParameterService = Depends(get_ho_class_param_service)):
    """Добавляет параметр в шаблон типа ХО (ADD_PARAM_TO_HO_CLASS)."""
    return service.create(data)


@router.delete("/class-parameters/{cp_id}", status_code=204)
def delete_class_param(cp_id: int, service: HoClassParameterService = Depends(get_ho_class_param_service)):
    service.delete(cp_id)
