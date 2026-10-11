from typing import Sequence

from src.core.errors import NotFoundError

from src.models.packaging import Packaging, PackagingNorm, PackagingType
from src.repository.packaging_repository import (
    PackagingNormRepository,
    PackagingRepository,
    PackagingTypeRepository,
)
from src.schemas.packaging import (
    PackagingCreate,
    PackagingNormCreate,
    PackagingTypeCreate,
    PackagingTypeUpdate,
    PackagingUpdate,
)


class PackagingTypeService:
    def __init__(self, repo: PackagingTypeRepository) -> None:
        self.repo = repo

    def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[PackagingType]:
        return self.repo.get_all(skip=skip, limit=limit)

    def get_by_id(self, obj_id: int) -> PackagingType:
        obj = self.repo.get_by_id(obj_id)
        if not obj:
            raise NotFoundError("PackagingType not found")
        return obj

    def create(self, data: PackagingTypeCreate) -> PackagingType:
        return self.repo.create(data.model_dump())

    def update(self, obj_id: int, data: PackagingTypeUpdate) -> PackagingType:
        obj = self.get_by_id(obj_id)
        return self.repo.update(obj, data.model_dump(exclude_none=True))

    def delete(self, obj_id: int) -> None:
        obj = self.get_by_id(obj_id)
        self.repo.delete(obj)


class PackagingService:
    def __init__(self, repo: PackagingRepository) -> None:
        self.repo = repo

    def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Packaging]:
        return self.repo.get_all(skip=skip, limit=limit)

    def get_by_id(self, obj_id: int) -> Packaging:
        obj = self.repo.get_by_id(obj_id)
        if not obj:
            raise NotFoundError("Packaging not found")
        return obj

    def create(self, data: PackagingCreate) -> Packaging:
        return self.repo.create(data.model_dump())

    def update(self, obj_id: int, data: PackagingUpdate) -> Packaging:
        obj = self.get_by_id(obj_id)
        return self.repo.update(obj, data.model_dump(exclude_none=True))

    def delete(self, obj_id: int) -> None:
        obj = self.get_by_id(obj_id)
        self.repo.delete(obj)


class PackagingNormService:
    def __init__(self, repo: PackagingNormRepository) -> None:
        self.repo = repo

    def get_by_item(self, item_id: int) -> Sequence[PackagingNorm]:
        return self.repo.get_by_item(item_id)

    def get_by_id(self, obj_id: int) -> PackagingNorm:
        obj = self.repo.get_by_id(obj_id)
        if not obj:
            raise NotFoundError("PackagingNorm not found")
        return obj

    def create(self, data: PackagingNormCreate) -> PackagingNorm:
        return self.repo.create(data.model_dump())

    def delete(self, obj_id: int) -> None:
        obj = self.get_by_id(obj_id)
        self.repo.delete(obj)
