from typing import Sequence, cast

from src.core.errors import ConflictError, NotFoundError

from src.models.positions import HoPosition, Pricelist, PricelistSet
from src.repository.ho_repository import PositionListRepository
from src.repository.position_repository import HoPositionRepository, PricelistRepository, PricelistSetRepository
from src.schemas.positions import HoPositionCreate, HoPositionUpdate, PricelistCreate, PricelistSetCreate


class PricelistSetService:
    def __init__(self, repo: PricelistSetRepository) -> None:
        self.repo = repo

    def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[PricelistSet]:
        return self.repo.get_all(skip=skip, limit=limit)

    def get_by_id(self, obj_id: int) -> PricelistSet:
        obj = self.repo.get_by_id(obj_id)
        if not obj:
            raise NotFoundError("PricelistSet not found")
        return obj

    def create(self, data: PricelistSetCreate) -> PricelistSet:
        return self.repo.create(data.model_dump())

    def delete(self, obj_id: int) -> None:
        obj = self.get_by_id(obj_id)
        self.repo.delete(obj)


class PricelistService:
    def __init__(self, repo: PricelistRepository) -> None:
        self.repo = repo

    def get_by_set(self, pricelist_set_id: int) -> Sequence[Pricelist]:
        return self.repo.get_by_set(pricelist_set_id)

    def get_by_id(self, obj_id: int) -> Pricelist:
        obj = self.repo.get_by_id(obj_id)
        if not obj:
            raise NotFoundError("Pricelist not found")
        return obj

    def create(self, data: PricelistCreate) -> Pricelist:
        if self.repo.get_by_set_and_item(data.pricelist_set_id, data.item_id):
            raise ConflictError("Item already in this pricelist")
        return self.repo.create(data.model_dump())

    def delete(self, obj_id: int) -> None:
        obj = self.get_by_id(obj_id)
        self.repo.delete(obj)


class HoPositionService:
    def __init__(
        self,
        position_repo: HoPositionRepository,
        position_list_repo: PositionListRepository,
    ) -> None:
        self.position_repo = position_repo
        self.position_list_repo = position_list_repo

    def get_by_ho(self, ho_id: int) -> Sequence[HoPosition]:
        """Возвращает позиции ХО через position_list."""
        pl = self.position_list_repo.get_by_ho(ho_id)
        if not pl:
            raise NotFoundError("PositionList not found for this HO")
        return self.position_repo.get_by_position_list(cast(int, pl.id))

    def get_by_id(self, obj_id: int) -> HoPosition:
        obj = self.position_repo.get_by_id(obj_id)
        if not obj:
            raise NotFoundError("HoPosition not found")
        return obj

    def add_position(self, ho_id: int, data: HoPositionCreate) -> HoPosition:
        """ADD_HO_POSITION: добавляет строку в табличную часть ХО."""
        pl = self.position_list_repo.get_by_ho(ho_id)
        if not pl:
            raise NotFoundError("PositionList not found for this HO")
        pos_data = data.model_dump()
        pos_data["position_list_id"] = pl.id
        return self.position_repo.create(pos_data)

    def update_position(self, pos_id: int, data: HoPositionUpdate) -> HoPosition:
        obj = self.get_by_id(pos_id)
        return self.position_repo.update(obj, data.model_dump(exclude_none=True))

    def delete_position(self, pos_id: int) -> None:
        obj = self.get_by_id(pos_id)
        self.position_repo.delete(obj)
