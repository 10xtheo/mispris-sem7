from typing import Optional

from sqlmodel import Session, select

from src.models.parameters import Parameter
from src.repository.base import BaseRepository


class ParameterRepository(BaseRepository[Parameter]):
    def __init__(self, session: Session) -> None:
        super().__init__(Parameter, session)

    def get_by_code(self, code: str) -> Optional[Parameter]:
        result = self.session.exec(select(Parameter).where(Parameter.code == code))
        return result.first()
