from typing import Optional

from sqlmodel import Session, select

from src.models.units import UnitSimple
from src.repository.base import BaseRepository


class UnitSimpleRepository(BaseRepository[UnitSimple]):
    def __init__(self, session: Session) -> None:
        super().__init__(UnitSimple, session)

    def get_by_code(self, code: str) -> Optional[UnitSimple]:
        result = self.session.exec(select(UnitSimple).where(UnitSimple.code == code))
        return result.first()
