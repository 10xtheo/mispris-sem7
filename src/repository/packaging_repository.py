from typing import Sequence

from sqlmodel import Session, select

from src.models.packaging import Packaging, PackagingNorm, PackagingType
from src.repository.base import BaseRepository


class PackagingTypeRepository(BaseRepository[PackagingType]):
    def __init__(self, session: Session) -> None:
        super().__init__(PackagingType, session)


class PackagingRepository(BaseRepository[Packaging]):
    def __init__(self, session: Session) -> None:
        super().__init__(Packaging, session)


class PackagingNormRepository(BaseRepository[PackagingNorm]):
    def __init__(self, session: Session) -> None:
        super().__init__(PackagingNorm, session)

    def get_by_item(self, item_id: int) -> Sequence[PackagingNorm]:
        result = self.session.exec(
            select(PackagingNorm).where(PackagingNorm.item_id == item_id)
        )
        return result.all()
