from typing import Optional, Sequence

from sqlmodel import Session, col, select

from src.models.items import Item, ItemBatch, UnitQuantity
from src.repository.base import BaseRepository


class ItemRepository(BaseRepository[Item]):
    def __init__(self, session: Session) -> None:
        super().__init__(Item, session)

    def get_by_number(self, number: str) -> Optional[Item]:
        result = self.session.exec(select(Item).where(Item.number == number))
        return result.first()

    def search_by_name(self, name: str) -> Sequence[Item]:
        result = self.session.exec(
            select(Item).where(col(Item.name).ilike(f"%{name}%"))
        )
        return result.all()


class UnitQuantityRepository(BaseRepository[UnitQuantity]):
    def __init__(self, session: Session) -> None:
        super().__init__(UnitQuantity, session)

    def get_by_item(self, item_id: int) -> Sequence[UnitQuantity]:
        result = self.session.exec(
            select(UnitQuantity).where(UnitQuantity.item_id == item_id)
        )
        return result.all()

    def get_base_unit(self, item_id: int) -> Optional[UnitQuantity]:
        result = self.session.exec(
            select(UnitQuantity).where(
                UnitQuantity.item_id == item_id, UnitQuantity.is_base == True
            )
        )
        return result.first()


class ItemBatchRepository(BaseRepository[ItemBatch]):
    def __init__(self, session: Session) -> None:
        super().__init__(ItemBatch, session)

    def get_by_item(self, item_id: int) -> Sequence[ItemBatch]:
        result = self.session.exec(
            select(ItemBatch).where(ItemBatch.item_id == item_id)
        )
        return result.all()
