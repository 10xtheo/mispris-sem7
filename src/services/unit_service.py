from typing import Sequence

from src.core.errors import ConflictError, NotFoundError

from src.models.units import UnitSimple
from src.repository.unit_repository import UnitSimpleRepository
from src.schemas.units import UnitSimpleCreate, UnitSimpleUpdate


class UnitSimpleService:
    def __init__(self, repo: UnitSimpleRepository) -> None:
        self.repo = repo

    def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[UnitSimple]:
        return self.repo.get_all(skip=skip, limit=limit)

    def get_by_id(self, obj_id: int) -> UnitSimple:
        obj = self.repo.get_by_id(obj_id)
        if not obj:
            raise NotFoundError("Unit not found")
        return obj

    def create(self, data: UnitSimpleCreate) -> UnitSimple:
        if self.repo.get_by_code(data.code):
            raise ConflictError(f"Unit with code '{data.code}' exists")
        return self.repo.create(data.model_dump())

    def update(self, obj_id: int, data: UnitSimpleUpdate) -> UnitSimple:
        obj = self.get_by_id(obj_id)
        return self.repo.update(obj, data.model_dump(exclude_none=True))

    def delete(self, obj_id: int) -> None:
        obj = self.get_by_id(obj_id)
        self.repo.delete(obj)
