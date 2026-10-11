from typing import Optional, Sequence

from sqlmodel import Session, col, select

from src.models.enums import EnumType, EnumValue
from src.repository.base import BaseRepository


class EnumTypeRepository(BaseRepository[EnumType]):
    def __init__(self, session: Session) -> None:
        super().__init__(EnumType, session)

    def get_by_code(self, code: str) -> Optional[EnumType]:
        result = self.session.exec(select(EnumType).where(EnumType.code == code))
        return result.first()


class EnumValueRepository(BaseRepository[EnumValue]):
    def __init__(self, session: Session) -> None:
        super().__init__(EnumValue, session)

    def get_by_type(self, enum_type_id: int) -> Sequence[EnumValue]:
        result = self.session.exec(
            select(EnumValue)
            .where(EnumValue.enum_type_id == enum_type_id)
            .order_by(col(EnumValue.order_number))
        )
        return result.all()

    def get_by_codes(self, type_code: str, value_code: str) -> Optional[EnumValue]:
        """Значение перечисления по коду типа и коду значения ('item_type', 'material')."""
        result = self.session.exec(
            select(EnumValue)
            .join(EnumType, EnumType.id == EnumValue.enum_type_id)  # type: ignore[arg-type]
            .where(EnumType.code == type_code, EnumValue.code == value_code)
        )
        return result.first()

    def get_by_type_and_code(self, enum_type_id: int, code: str) -> Optional[EnumValue]:
        result = self.session.exec(
            select(EnumValue).where(
                EnumValue.enum_type_id == enum_type_id,
                EnumValue.code == code,
            )
        )
        return result.first()
