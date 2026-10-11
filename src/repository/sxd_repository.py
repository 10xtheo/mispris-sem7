from typing import Optional, Sequence

from sqlmodel import Session, col, select

from src.models.sxd import Sxd
from src.repository.base import BaseRepository


class SxdRepository(BaseRepository[Sxd]):
    def __init__(self, session: Session) -> None:
        super().__init__(Sxd, session)

    def get_by_class(self, sxd_class_id: int) -> Sequence[Sxd]:
        result = self.session.exec(
            select(Sxd).where(Sxd.sxd_class_id == sxd_class_id)
        )
        return result.all()

    def search_by_name(self, name: str) -> Sequence[Sxd]:
        result = self.session.exec(
            select(Sxd).where(col(Sxd.name).ilike(f"%{name}%"))
        )
        return result.all()
