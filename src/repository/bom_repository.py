from datetime import datetime
from typing import Any, Iterable, Optional, Sequence

from sqlmodel import Session, col, or_, select

from src.models.bom import ItemBom, ItemChange
from src.models.classifiers import ItemClassifier
from src.models.enums import EnumValue
from src.models.items import Item, UnitQuantity
from src.models.units import UnitSimple
from src.repository.base import BaseRepository


class ItemBomRepository(BaseRepository[ItemBom]):
    """Позиции материальной спецификации и справочные данные для расчётов состава."""

    def __init__(self, session: Session) -> None:
        super().__init__(ItemBom, session)

    def get_own_active(self, parent_item_id: int, component_item_id: int) -> Optional[ItemBom]:
        """Действующая собственная строка изделия по компоненту (в т.ч. строка-исключение)."""
        result = self.session.exec(
            select(ItemBom).where(
                ItemBom.parent_item_id == parent_item_id,
                ItemBom.component_item_id == component_item_id,
                col(ItemBom.valid_to).is_(None),
            )
        )
        return result.first()

    def count_own_active(self, parent_item_id: int) -> int:
        result = self.session.exec(
            select(ItemBom).where(
                ItemBom.parent_item_id == parent_item_id,
                col(ItemBom.valid_to).is_(None),
                ItemBom.is_excluded == False,  # noqa: E712
            )
        )
        return len(result.all())

    def close(self, row: ItemBom, at: datetime) -> ItemBom:
        """Закрыть версию строки (valid_to) вместо физического изменения."""
        return self.update(row, {"valid_to": at})

    def rows_at(self, parent_item_ids: Iterable[int], at: datetime) -> Sequence[ItemBom]:
        """Версии позиций изделий, действовавшие в момент at."""
        ids = list(parent_item_ids)
        if not ids:
            return []
        result = self.session.exec(
            select(ItemBom).where(
                col(ItemBom.parent_item_id).in_(ids),
                ItemBom.valid_from <= at,
                or_(col(ItemBom.valid_to).is_(None), col(ItemBom.valid_to) > at),
            )
        )
        return result.all()

    def get_many(self, bom_ids: Iterable[int]) -> dict[int, ItemBom]:
        ids = [i for i in bom_ids if i is not None]
        if not ids:
            return {}
        return {r.id: r for r in self.session.exec(select(ItemBom).where(col(ItemBom.id).in_(ids))).all()}


class ItemCatalogRepository:
    """Справочные сведения об изделиях для расчётов и вывода спецификаций."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def base_item_id(self, item_id: int) -> Optional[int]:
        item = self.session.get(Item, item_id)
        return item.base_item_id if item else None

    def modification_ids(self, base_item_id: int) -> list[int]:
        result = self.session.exec(select(Item.id).where(Item.base_item_id == base_item_id))
        return [i for i in result.all() if i is not None]

    def class_children(self, class_id: int) -> list[int]:
        result = self.session.exec(select(ItemClassifier.id).where(ItemClassifier.parent_id == class_id))
        return [i for i in result.all() if i is not None]

    def item_info(self, item_ids: Iterable[int]) -> dict[int, dict[str, Any]]:
        """Обозначение, наименование, тип, класс и базовая ЕИ изделий."""
        ids = list(set(item_ids))
        if not ids:
            return {}
        items = self.session.exec(select(Item).where(col(Item.id).in_(ids))).all()
        classes = {c.id: c.name for c in self.session.exec(select(ItemClassifier)).all()}
        types = {
            e.id: e.code
            for e in self.session.exec(
                select(EnumValue).where(col(EnumValue.id).in_([i.item_type_id for i in items if i.item_type_id]))
            ).all()
        }
        base_units = {}
        rows = self.session.exec(
            select(UnitQuantity, UnitSimple)
            .join(UnitSimple, UnitSimple.id == UnitQuantity.unit_simple_id)  # type: ignore[arg-type]
            .where(col(UnitQuantity.item_id).in_(ids), UnitQuantity.is_base == True)  # noqa: E712
            .order_by(col(UnitQuantity.id))
        ).all()
        for uq, us in rows:
            base_units.setdefault(uq.item_id, us.cond_symbol_1)
        return {
            i.id: {
                "component_number": i.number,
                "component_name": i.name,
                "component_type": types.get(i.item_type_id),
                "class_id": i.item_class_id,
                "class_name": classes.get(i.item_class_id),
                "base_unit_symbol": base_units.get(i.id),
            }
            for i in items
        }

    def unit_info(self, unit_quantity_ids: Iterable[int]) -> dict[int, tuple[Any, Optional[str]]]:
        """Коэффициент пересчёта к базовой ЕИ и обозначение для ЕИ количества."""
        ids = [i for i in set(unit_quantity_ids) if i is not None]
        if not ids:
            return {}
        rows = self.session.exec(
            select(UnitQuantity, UnitSimple)
            .join(UnitSimple, UnitSimple.id == UnitQuantity.unit_simple_id)  # type: ignore[arg-type]
            .where(col(UnitQuantity.id).in_(ids))
        ).all()
        return {uq.id: (uq.coefficient, us.cond_symbol_1) for uq, us in rows}

    def enum_values(self, ids: Iterable[int]) -> dict[int, EnumValue]:
        ids = list(set(ids))
        if not ids:
            return {}
        return {e.id: e for e in self.session.exec(select(EnumValue).where(col(EnumValue.id).in_(ids))).all()}


class ItemChangeRepository(BaseRepository[ItemChange]):
    def __init__(self, session: Session) -> None:
        super().__init__(ItemChange, session)

    def by_item(self, item_id: int) -> Sequence[ItemChange]:
        result = self.session.exec(
            select(ItemChange)
            .where(ItemChange.item_id == item_id)
            .order_by(col(ItemChange.change_date), col(ItemChange.id))
        )
        return result.all()


class ModificationRepository:
    """Запросы по модификациям (Item с base_item_id)."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_modifications(self, base_item_id: int) -> Sequence[Item]:
        result = self.session.exec(
            select(Item).where(Item.base_item_id == base_item_id).order_by(col(Item.id))
        )
        return result.all()
