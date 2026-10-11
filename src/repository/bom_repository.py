from datetime import datetime
from decimal import Decimal
from typing import Any, Optional, Sequence

from sqlalchemy import text
from sqlmodel import Session, col, select

from src.models.bom import ItemBom, ItemChange
from src.models.items import Item
from src.repository.base import BaseRepository

# Реквизиты компонента для отображения: обозначение, тип, класс, ЕИ строки и базовая ЕИ
_COMPONENT_JOINS = """
    JOIN item i ON i.id = r.component_item_id
    LEFT JOIN item_classifier ic ON ic.id = i.item_class_id
    LEFT JOIN enum_value tv ON tv.id = i.item_type_id
    LEFT JOIN unit_quantity uq ON uq.id = r.unit_quantity_id
    LEFT JOIN unit_simple us ON us.id = uq.unit_simple_id
    LEFT JOIN LATERAL (
        SELECT bs.cond_symbol_1 AS base_unit_symbol
        FROM unit_quantity bq JOIN unit_simple bs ON bs.id = bq.unit_simple_id
        WHERE bq.item_id = i.id AND bq.is_base
        ORDER BY bq.id LIMIT 1
    ) bu ON true
"""

_COMPONENT_COLUMNS = """
    i.number AS component_number, i.name AS component_name,
    i.item_class_id AS class_id, ic.name AS class_name,
    tv.code AS component_type, us.cond_symbol_1 AS unit_symbol, bu.base_unit_symbol
"""


class ItemBomRepository(BaseRepository[ItemBom]):
    """Позиции спецификации и обёртки над SQL-функциями effective_bom / find_bom / calc_bom."""

    def __init__(self, session: Session) -> None:
        super().__init__(ItemBom, session)

    def _rows(self, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        return [dict(r) for r in self.session.execute(text(sql), params).mappings().all()]

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

    def effective(
        self, item_id: int, at: datetime, include_excluded: bool = False
    ) -> list[dict[str, Any]]:
        """Действующая спецификация изделия (один уровень) с учётом модификаций."""
        sql = f"""
            SELECT r.*, (r.owner_item_id <> :item_id) AS inherited, {_COMPONENT_COLUMNS}
            FROM effective_bom(:item_id, :at, :inc) r
            {_COMPONENT_JOINS}
            ORDER BY r.order_number, r.component_item_id
        """
        return self._rows(sql, {"item_id": item_id, "at": at, "inc": include_excluded})

    def effective_row(self, item_id: int, component_item_id: int, at: datetime) -> Optional[dict[str, Any]]:
        for row in self.effective(item_id, at):
            if row["component_item_id"] == component_item_id:
                return row
        return None

    def find_bom(self, item_id: int, at: datetime) -> list[dict[str, Any]]:
        """FIND_BOM — полный состав на всю глубину вложенности."""
        sql = f"""
            SELECT r.*, {_COMPONENT_COLUMNS}
            FROM find_bom(:item_id, :at) r
            {_COMPONENT_JOINS}
            ORDER BY r.sort_path
        """
        return self._rows(sql, {"item_id": item_id, "at": at})

    def calc_bom(
        self, item_id: int, quantity: Decimal, class_id: Optional[int], at: datetime
    ) -> list[dict[str, Any]]:
        """CALC_BOM — сводные нормы расхода на заданное количество изделия."""
        sql = """
            SELECT r.component_item_id, r.total_quantity,
                   i.number AS component_number, i.name AS component_name,
                   i.item_class_id AS class_id, ic.name AS class_name,
                   tv.code AS component_type, bu.base_unit_symbol
            FROM calc_bom(:item_id, :qty, :class_id, :at) r
            JOIN item i ON i.id = r.component_item_id
            LEFT JOIN item_classifier ic ON ic.id = i.item_class_id
            LEFT JOIN enum_value tv ON tv.id = i.item_type_id
            LEFT JOIN LATERAL (
                SELECT bs.cond_symbol_1 AS base_unit_symbol
                FROM unit_quantity bq JOIN unit_simple bs ON bs.id = bq.unit_simple_id
                WHERE bq.item_id = i.id AND bq.is_base
                ORDER BY bq.id LIMIT 1
            ) bu ON true
            ORDER BY ic.name NULLS LAST, i.name
        """
        return self._rows(sql, {"item_id": item_id, "qty": quantity, "class_id": class_id, "at": at})

    def has_cycle(self, item_id: int, at: datetime) -> bool:
        return bool(
            self.session.execute(
                text("SELECT bom_has_cycle(:item_id, :at)"), {"item_id": item_id, "at": at}
            ).scalar_one()
        )


class ItemChangeRepository(BaseRepository[ItemChange]):
    def __init__(self, session: Session) -> None:
        super().__init__(ItemChange, session)

    def history(self, item_id: int) -> list[dict[str, Any]]:
        """История изменений спецификации с версиями строк «было» и «стало»."""
        sql = """
            SELECT c.id, c.item_id, c.change_date, c.reason,
                   ct.code AS change_type, ct.name AS change_type_name,
                   ob.id AS old_bom_id, ob.component_item_id AS old_component_item_id,
                   oi.name AS old_component_name, ob.quantity AS old_quantity,
                   ob.for_quantity AS old_for_quantity, ob.is_excluded AS old_is_excluded,
                   ob.valid_from AS old_valid_from, ob.valid_to AS old_valid_to,
                   nb.id AS new_bom_id, nb.component_item_id AS new_component_item_id,
                   ni.name AS new_component_name, nb.quantity AS new_quantity,
                   nb.for_quantity AS new_for_quantity, nb.is_excluded AS new_is_excluded,
                   nb.valid_from AS new_valid_from, nb.valid_to AS new_valid_to
            FROM item_change c
            JOIN enum_value ct ON ct.id = c.change_type_id
            LEFT JOIN item_bom ob ON ob.id = c.old_bom_id
            LEFT JOIN item oi ON oi.id = ob.component_item_id
            LEFT JOIN item_bom nb ON nb.id = c.new_bom_id
            LEFT JOIN item ni ON ni.id = nb.component_item_id
            WHERE c.item_id = :item_id
            ORDER BY c.change_date, c.id
        """
        return [dict(r) for r in self.session.execute(text(sql), {"item_id": item_id}).mappings().all()]


class ModificationRepository:
    """Запросы по модификациям (Item с base_item_id)."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_modifications(self, base_item_id: int) -> Sequence[Item]:
        result = self.session.exec(
            select(Item).where(Item.base_item_id == base_item_id).order_by(col(Item.id))
        )
        return result.all()
