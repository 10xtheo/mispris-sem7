from typing import Sequence

from src.core.errors import ConflictError, NotFoundError

from src.models.roles import AvailableRoles, SxdRole
from src.repository.role_repository import AvailableRolesRepository, SxdRoleRepository
from src.schemas.roles import AvailableRoleCreate, AvailableRoleUpdate, SxdRoleCreate, SxdRoleUpdate


class SxdRoleService:
    def __init__(self, repo: SxdRoleRepository) -> None:
        self.repo = repo

    def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[SxdRole]:
        return self.repo.get_all(skip=skip, limit=limit)

    def get_by_id(self, obj_id: int) -> SxdRole:
        obj = self.repo.get_by_id(obj_id)
        if not obj:
            raise NotFoundError("SxdRole not found")
        return obj

    def create(self, data: SxdRoleCreate) -> SxdRole:
        return self.repo.create(data.model_dump())

    def update(self, obj_id: int, data: SxdRoleUpdate) -> SxdRole:
        obj = self.get_by_id(obj_id)
        return self.repo.update(obj, data.model_dump(exclude_none=True))

    def delete(self, obj_id: int) -> None:
        obj = self.get_by_id(obj_id)
        self.repo.delete(obj)


class AvailableRolesService:
    def __init__(self, repo: AvailableRolesRepository) -> None:
        self.repo = repo

    def get_by_ho_type(self, ho_type_id: int) -> Sequence[AvailableRoles]:
        return self.repo.get_by_ho_type(ho_type_id)

    def get_by_id(self, obj_id: int) -> AvailableRoles:
        obj = self.repo.get_by_id(obj_id)
        if not obj:
            raise NotFoundError("AvailableRole not found")
        return obj

    def create(self, data: AvailableRoleCreate) -> AvailableRoles:
        if self.repo.get_by_ho_type_and_role(data.ho_type_id, data.role_id):
            raise ConflictError("Role already assigned to this HO type")
        return self.repo.create(data.model_dump())

    def update(self, obj_id: int, data: AvailableRoleUpdate) -> AvailableRoles:
        obj = self.get_by_id(obj_id)
        return self.repo.update(obj, data.model_dump(exclude_none=True))

    def delete(self, obj_id: int) -> None:
        obj = self.get_by_id(obj_id)
        self.repo.delete(obj)
