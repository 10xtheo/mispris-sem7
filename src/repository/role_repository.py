from typing import Optional, Sequence

from sqlmodel import Session, select

from src.models.roles import AvailableRoles, SxdRole
from src.repository.base import BaseRepository


class SxdRoleRepository(BaseRepository[SxdRole]):
    def __init__(self, session: Session) -> None:
        super().__init__(SxdRole, session)


class AvailableRolesRepository(BaseRepository[AvailableRoles]):
    def __init__(self, session: Session) -> None:
        super().__init__(AvailableRoles, session)

    def get_by_ho_type(self, ho_type_id: int) -> Sequence[AvailableRoles]:
        result = self.session.exec(
            select(AvailableRoles).where(AvailableRoles.ho_type_id == ho_type_id)
        )
        return result.all()

    def get_by_ho_type_and_role(self, ho_type_id: int, role_id: int) -> Optional[AvailableRoles]:
        result = self.session.exec(
            select(AvailableRoles).where(
                AvailableRoles.ho_type_id == ho_type_id,
                AvailableRoles.role_id == role_id,
            )
        )
        return result.first()
