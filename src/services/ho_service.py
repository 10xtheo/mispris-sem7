from typing import List, Optional, Sequence, cast

from src.core.errors import BusinessRuleError, ConflictError, NotFoundError

from src.models.ho import Ho, SxdRoleInHo
from src.models.param_values import HoParameterValue
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
    HoCreate,
    HoParameterValueRead,
    HoParameterValueWrite,
    HoReadFull,
    HoSearchParams,
    HoUpdate,
    SxdRoleInHoCreate,
    SxdRoleInHoRead,
)


class HoService:
    def __init__(
        self,
        ho_repo: HoRepository,
        ho_class_param_repo: HoClassParameterRepository,
        ho_param_value_repo: HoParameterValueRepository,
        role_in_ho_repo: SxdRoleInHoRepository,
        available_roles_repo: AvailableRolesRepository,
        position_list_repo: PositionListRepository,
        param_repo: ParameterRepository,
        enum_value_repo: EnumValueRepository,
    ) -> None:
        self.ho_repo = ho_repo
        self.ho_class_param_repo = ho_class_param_repo
        self.ho_param_value_repo = ho_param_value_repo
        self.role_in_ho_repo = role_in_ho_repo
        self.available_roles_repo = available_roles_repo
        self.position_list_repo = position_list_repo
        self.param_repo = param_repo
        self.enum_value_repo = enum_value_repo

    def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Ho]:
        return self.ho_repo.get_all(skip=skip, limit=limit)

    def get_by_id(self, ho_id: int) -> Ho:
        obj = self.ho_repo.get_by_id(ho_id)
        if not obj:
            raise NotFoundError("HO not found")
        return obj

    def search(self, params: HoSearchParams) -> Sequence[Ho]:
        """Поиск ХО по классу, дате, номеру документа (FIND_HO_BY_CLASS)."""
        return self.ho_repo.search(
            ho_type_id=params.ho_type_id,
            date_from=params.date_from,
            date_to=params.date_to,
            document_number=params.document_number,
            skip=params.skip,
            limit=params.limit,
        )

    def create(self, data: HoCreate) -> Ho:
        """
        INS_HO: создаёт ХО, инициализирует position_list
        и заготовки ho_parameter_value для всех параметров типа.
        """
        ho = self.ho_repo.create(data.model_dump())
        self.position_list_repo.create({"ho_id": ho.id})
        class_params = self.ho_class_param_repo.get_by_ho_type(data.ho_type_id)
        for cp in class_params:
            self.ho_param_value_repo.create({"ho_id": ho.id, "ho_class_param_id": cp.id})
        return ho

    def update(self, ho_id: int, data: HoUpdate) -> Ho:
        obj = self.get_by_id(ho_id)
        return self.ho_repo.update(obj, data.model_dump(exclude_none=True))

    def delete(self, ho_id: int) -> None:
        obj = self.get_by_id(ho_id)
        self.ho_repo.delete(obj)

    def get_full(self, ho_id: int) -> HoReadFull:
        """Полное представление ХО: параметры с именами, роли."""
        ho = self.get_by_id(ho_id)
        return HoReadFull(
            id=cast(int, ho.id),
            ho_type_id=ho.ho_type_id,
            document_number=ho.document_number,
            op_date=ho.op_date,
            amount=ho.amount,
            parameters=self.get_parameter_values(ho_id),
            roles=self.get_roles(ho_id),
        )

    def get_parameter_values(self, ho_id: int) -> List[HoParameterValueRead]:
        """Значения параметров ХО с именами параметров."""
        self.get_by_id(ho_id)
        values = self.ho_param_value_repo.get_by_ho(ho_id)
        result = []
        for v in values:
            cp = self.ho_class_param_repo.get_by_id(v.ho_class_param_id)
            param_name, param_code = None, None
            if cp:
                param = self.param_repo.get_by_id(cp.parameter_id)
                if param:
                    param_name = param.name
                    param_code = param.code
            result.append(
                HoParameterValueRead(
                    id=cast(int, v.id),
                    ho_id=v.ho_id,
                    ho_class_param_id=v.ho_class_param_id,
                    value_str=v.value_str,
                    value_int=v.value_int,
                    value_real=v.value_real,
                    value_dt=v.value_dt,
                    value_enum_id=v.value_enum_id,
                    parameter_name=param_name,
                    parameter_code=param_code,
                )
            )
        return result

    def write_parameter_value(
        self, ho_id: int, ho_class_param_id: int, data: HoParameterValueWrite
    ) -> HoParameterValue:
        """WRITE_HO_PAR: записывает значение параметра с валидацией типа и диапазона."""
        self.get_by_id(ho_id)

        cp = self.ho_class_param_repo.get_by_id(ho_class_param_id)
        if not cp:
            raise NotFoundError("HoClassParameter not found")
        param = self.param_repo.get_by_id(cp.parameter_id)
        if not param:
            raise NotFoundError("Parameter not found")
        param_type_ev = self.enum_value_repo.get_by_id(param.param_type_id)
        param_type_code = param_type_ev.code if param_type_ev else None

        if param_type_code == "number":
            val = data.value_real if data.value_real is not None else data.value_int
            if val is not None:
                if cp.min_value is not None and val < cp.min_value:
                    raise BusinessRuleError(f"Value below minimum {cp.min_value}")
                if cp.max_value is not None and val > cp.max_value:
                    raise BusinessRuleError(f"Value above maximum {cp.max_value}")
        elif param_type_code == "enum" and data.value_enum_id is not None:
            ev = self.enum_value_repo.get_by_id(data.value_enum_id)
            if not ev or ev.enum_type_id != param.enum_type_id:
                raise BusinessRuleError("Invalid enum value for this parameter")
        existing = self.ho_param_value_repo.get_by_ho_and_class_param(ho_id, ho_class_param_id)
        update_data = data.model_dump()
        update_data.update({"ho_id": ho_id, "ho_class_param_id": ho_class_param_id})

        if existing:
            return self.ho_param_value_repo.update(existing, data.model_dump())
        return self.ho_param_value_repo.create(update_data)

    def get_roles(self, ho_id: int) -> List[SxdRoleInHoRead]:
        """Назначения ролей ХО."""
        self.get_by_id(ho_id)
        assignments = self.role_in_ho_repo.get_by_ho(ho_id)
        return [
            SxdRoleInHoRead(id=cast(int, a.id), ho_id=a.ho_id, sxd_id=a.sxd_id, role_id=a.role_id)
            for a in assignments
        ]

    def assign_role(self, ho_id: int, data: SxdRoleInHoCreate) -> SxdRoleInHo:
        """SET_HO_ACTOR: назначает СХД на роль с проверкой available_roles и max_count."""
        ho = self.get_by_id(ho_id)

        avail = self.available_roles_repo.get_by_ho_type_and_role(ho.ho_type_id, data.role_id)
        if not avail:
            raise BusinessRuleError(f"Role {data.role_id} is not available for HO type {ho.ho_type_id}")
        if avail.max_count is not None:
            current_count = self.role_in_ho_repo.count_by_ho_and_role(ho_id, data.role_id)
            if current_count >= avail.max_count:
                raise BusinessRuleError(f"Maximum actors for this role reached ({avail.max_count})")
        if self.role_in_ho_repo.get_by_ho_sxd_role(ho_id, data.sxd_id, data.role_id):
            raise ConflictError("This SXD already has this role in this HO")
        return self.role_in_ho_repo.create(
            {"ho_id": ho_id, "sxd_id": data.sxd_id, "role_id": data.role_id}
        )

    def remove_role(self, ho_id: int, sxd_id: int, role_id: int) -> None:
        assignment = self.role_in_ho_repo.get_by_ho_sxd_role(ho_id, sxd_id, role_id)
        if not assignment:
            raise NotFoundError("Role assignment not found")
        self.role_in_ho_repo.delete(assignment)


class HoClassParameterService:
    def __init__(self, repo: HoClassParameterRepository) -> None:
        self.repo = repo

    def get_by_ho_type(self, ho_type_id: int):
        return self.repo.get_by_ho_type(ho_type_id)

    def get_by_id(self, obj_id: int):
        obj = self.repo.get_by_id(obj_id)
        if not obj:
            raise NotFoundError("HoClassParameter not found")
        return obj

    def create(self, data: HoClassParameterCreate):
        if self.repo.get_by_ho_type_and_param(data.ho_type_id, data.parameter_id):
            raise ConflictError("Parameter already assigned to this HO type")
        return self.repo.create(data.model_dump())

    def delete(self, obj_id: int) -> None:
        obj = self.get_by_id(obj_id)
        self.repo.delete(obj)
