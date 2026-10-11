from datetime import date
from typing import Optional, Sequence

from sqlmodel import Session, col, select

from src.models.ho import DocClassParameter, Ho, HoClassParameter, SxdRoleInHo
from src.models.param_values import HoParameterValue
from src.models.positions import PositionList
from src.repository.base import BaseRepository


class HoRepository(BaseRepository[Ho]):
    def __init__(self, session: Session) -> None:
        super().__init__(Ho, session)

    def search(
        self,
        ho_type_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        document_number: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Ho]:
        stmt = select(Ho)
        if ho_type_id is not None:
            stmt = stmt.where(Ho.ho_type_id == ho_type_id)
        if date_from is not None:
            stmt = stmt.where(Ho.op_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(Ho.op_date <= date_to)
        if document_number is not None:
            stmt = stmt.where(col(Ho.document_number).ilike(f"%{document_number}%"))
        result = self.session.exec(stmt.offset(skip).limit(limit))
        return result.all()


class HoClassParameterRepository(BaseRepository[HoClassParameter]):
    def __init__(self, session: Session) -> None:
        super().__init__(HoClassParameter, session)

    def get_by_ho_type(self, ho_type_id: int) -> Sequence[HoClassParameter]:
        result = self.session.exec(
            select(HoClassParameter)
            .where(HoClassParameter.ho_type_id == ho_type_id)
            .order_by(col(HoClassParameter.display_order))
        )
        return result.all()

    def get_by_ho_type_and_param(self, ho_type_id: int, parameter_id: int) -> Optional[HoClassParameter]:
        result = self.session.exec(
            select(HoClassParameter).where(
                HoClassParameter.ho_type_id == ho_type_id,
                HoClassParameter.parameter_id == parameter_id,
            )
        )
        return result.first()


class HoParameterValueRepository(BaseRepository[HoParameterValue]):
    def __init__(self, session: Session) -> None:
        super().__init__(HoParameterValue, session)

    def get_by_ho(self, ho_id: int) -> Sequence[HoParameterValue]:
        result = self.session.exec(
            select(HoParameterValue).where(HoParameterValue.ho_id == ho_id)
        )
        return result.all()

    def get_by_ho_and_class_param(self, ho_id: int, ho_class_param_id: int) -> Optional[HoParameterValue]:
        result = self.session.exec(
            select(HoParameterValue).where(
                HoParameterValue.ho_id == ho_id,
                HoParameterValue.ho_class_param_id == ho_class_param_id,
            )
        )
        return result.first()


class SxdRoleInHoRepository(BaseRepository[SxdRoleInHo]):
    def __init__(self, session: Session) -> None:
        super().__init__(SxdRoleInHo, session)

    def get_by_ho(self, ho_id: int) -> Sequence[SxdRoleInHo]:
        result = self.session.exec(
            select(SxdRoleInHo).where(SxdRoleInHo.ho_id == ho_id)
        )
        return result.all()

    def count_by_ho_and_role(self, ho_id: int, role_id: int) -> int:
        result = self.session.exec(
            select(SxdRoleInHo).where(
                SxdRoleInHo.ho_id == ho_id,
                SxdRoleInHo.role_id == role_id,
            )
        )
        return len(result.all())

    def get_by_ho_sxd_role(self, ho_id: int, sxd_id: int, role_id: int) -> Optional[SxdRoleInHo]:
        result = self.session.exec(
            select(SxdRoleInHo).where(
                SxdRoleInHo.ho_id == ho_id,
                SxdRoleInHo.sxd_id == sxd_id,
                SxdRoleInHo.role_id == role_id,
            )
        )
        return result.first()


class PositionListRepository(BaseRepository[PositionList]):
    def __init__(self, session: Session) -> None:
        super().__init__(PositionList, session)

    def get_by_ho(self, ho_id: int) -> Optional[PositionList]:
        result = self.session.exec(
            select(PositionList).where(PositionList.ho_id == ho_id)
        )
        return result.first()


class DocClassParameterRepository(BaseRepository[DocClassParameter]):
    def __init__(self, session: Session) -> None:
        super().__init__(DocClassParameter, session)

    def get_by_doc_type(self, doc_type_id: int) -> Sequence[DocClassParameter]:
        result = self.session.exec(
            select(DocClassParameter)
            .where(DocClassParameter.doc_type_id == doc_type_id)
            .order_by(col(DocClassParameter.display_order))
        )
        return result.all()
