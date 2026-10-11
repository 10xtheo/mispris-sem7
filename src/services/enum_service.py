from typing import Sequence

from src.core.errors import ConflictError, NotFoundError

from src.models.enums import EnumType, EnumValue
from src.repository.enum_repository import EnumTypeRepository, EnumValueRepository
from src.schemas.enums import EnumTypeCreate, EnumTypeUpdate, EnumValueCreate, EnumValueUpdate


class EnumTypeService:
    def __init__(self, repo: EnumTypeRepository) -> None:
        self.repo = repo

    def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[EnumType]:
        return self.repo.get_all(skip=skip, limit=limit)

    def get_by_id(self, obj_id: int) -> EnumType:
        obj = self.repo.get_by_id(obj_id)
        if not obj:
            raise NotFoundError("EnumType not found")
        return obj

    def create(self, data: EnumTypeCreate) -> EnumType:
        if self.repo.get_by_code(data.code):
            raise ConflictError(f"EnumType with code '{data.code}' exists")
        return self.repo.create(data.model_dump())

    def update(self, obj_id: int, data: EnumTypeUpdate) -> EnumType:
        obj = self.get_by_id(obj_id)
        return self.repo.update(obj, data.model_dump(exclude_none=True))

    def delete(self, obj_id: int) -> None:
        obj = self.get_by_id(obj_id)
        self.repo.delete(obj)


class EnumValueService:
    def __init__(self, repo: EnumValueRepository) -> None:
        self.repo = repo

    def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[EnumValue]:
        return self.repo.get_all(skip=skip, limit=limit)

    def get_by_id(self, obj_id: int) -> EnumValue:
        obj = self.repo.get_by_id(obj_id)
        if not obj:
            raise NotFoundError("EnumValue not found")
        return obj

    def get_by_type(self, enum_type_id: int) -> Sequence[EnumValue]:
        return self.repo.get_by_type(enum_type_id)

    def create(self, data: EnumValueCreate) -> EnumValue:
        return self.repo.create(data.model_dump())

    def update(self, obj_id: int, data: EnumValueUpdate) -> EnumValue:
        obj = self.get_by_id(obj_id)
        return self.repo.update(obj, data.model_dump(exclude_none=True))

    def delete(self, obj_id: int) -> None:
        obj = self.get_by_id(obj_id)
        self.repo.delete(obj)
