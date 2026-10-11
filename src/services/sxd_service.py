from typing import Sequence

from src.core.errors import NotFoundError

from src.models.sxd import Sxd
from src.repository.sxd_repository import SxdRepository
from src.schemas.sxd import SxdCreate, SxdUpdate


class SxdService:
    def __init__(self, repo: SxdRepository) -> None:
        self.repo = repo

    def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Sxd]:
        return self.repo.get_all(skip=skip, limit=limit)

    def get_by_id(self, obj_id: int) -> Sxd:
        obj = self.repo.get_by_id(obj_id)
        if not obj:
            raise NotFoundError("SXD not found")
        return obj

    def search(self, name: str) -> Sequence[Sxd]:
        return self.repo.search_by_name(name)

    def create(self, data: SxdCreate) -> Sxd:
        return self.repo.create(data.model_dump())

    def update(self, obj_id: int, data: SxdUpdate) -> Sxd:
        obj = self.get_by_id(obj_id)
        return self.repo.update(obj, data.model_dump(exclude_none=True))

    def delete(self, obj_id: int) -> None:
        obj = self.get_by_id(obj_id)
        self.repo.delete(obj)
