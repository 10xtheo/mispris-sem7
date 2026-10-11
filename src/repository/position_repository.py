from typing import Sequence

from sqlmodel import Session, select

from src.models.positions import HoPosition, Pricelist, PricelistSet
from src.repository.base import BaseRepository


class PricelistSetRepository(BaseRepository[PricelistSet]):
    def __init__(self, session: Session) -> None:
        super().__init__(PricelistSet, session)


class PricelistRepository(BaseRepository[Pricelist]):
    def __init__(self, session: Session) -> None:
        super().__init__(Pricelist, session)

    def get_by_set(self, pricelist_set_id: int) -> Sequence[Pricelist]:
        result = self.session.exec(
            select(Pricelist).where(Pricelist.pricelist_set_id == pricelist_set_id)
        )
        return result.all()

    def get_by_set_and_item(self, pricelist_set_id: int, item_id: int) -> Pricelist | None:
        result = self.session.exec(
            select(Pricelist).where(
                Pricelist.pricelist_set_id == pricelist_set_id,
                Pricelist.item_id == item_id,
            )
        )
        return result.first()


class HoPositionRepository(BaseRepository[HoPosition]):
    def __init__(self, session: Session) -> None:
        super().__init__(HoPosition, session)

    def get_by_position_list(self, position_list_id: int) -> Sequence[HoPosition]:
        result = self.session.exec(
            select(HoPosition).where(HoPosition.position_list_id == position_list_id)
        )
        return result.all()
