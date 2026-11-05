"""Задание №5: спецификация изделий (BOM), модификации, история изменений

Revision ID: 002
Revises: 001
Create Date: 2026-10-11 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# --------------------------------------------------------------------------
# Справочные перечисления, без которых не работает бизнес-логика №5
# --------------------------------------------------------------------------
REFERENCE_ENUMS = {
    ("item_type", "Тип изделия"): [
        ("material", "Материал"),
        ("detail", "Деталь (полуфабрикат)"),
        ("assembly", "Сборочная единица"),
        ("complex", "Комплекс"),
    ],
    ("bom_change_type", "Тип изменения спецификации"): [
        ("add_component", "Добавление компонента"),
        ("change_quantity", "Изменение нормы расхода"),
        ("replace_component", "Замена компонента"),
        ("remove_component", "Удаление компонента"),
        ("create_modification", "Создание модификации"),
    ],
}


def upgrade() -> None:
    # 1. Изделие: тип и ссылка на базовое изделие (модификации)
    op.add_column("item", sa.Column("item_type_id", sa.Integer(), nullable=True))
    op.add_column("item", sa.Column("base_item_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_item_type", "item", "enum_value", ["item_type_id"], ["id"])
    op.create_foreign_key("fk_item_base_item", "item", "item", ["base_item_id"], ["id"], ondelete="RESTRICT")
    op.create_check_constraint("ck_item_not_own_base", "item", "base_item_id IS NULL OR base_item_id <> id")
    op.create_index("ix_item_base_item", "item", ["base_item_id"])

    # 2. Позиция материальной спецификации
    op.create_table(
        "item_bom",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("parent_item_id", sa.Integer(), nullable=False),
        sa.Column("component_item_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("for_quantity", sa.Numeric(18, 6), nullable=False, server_default="1"),
        sa.Column("unit_quantity_id", sa.Integer(), nullable=True),
        sa.Column("is_base", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_excluded", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("order_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["parent_item_id"], ["item.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["component_item_id"], ["item.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["unit_quantity_id"], ["unit_quantity.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("parent_item_id <> component_item_id", name="ck_item_bom_not_self"),
        sa.CheckConstraint("quantity > 0 OR is_excluded", name="ck_item_bom_quantity_positive"),
        sa.CheckConstraint("for_quantity > 0", name="ck_item_bom_for_quantity_positive"),
        sa.CheckConstraint("valid_to IS NULL OR valid_to >= valid_from", name="ck_item_bom_valid_period"),
    )
    op.create_index(
        "ux_item_bom_active_component", "item_bom", ["parent_item_id", "component_item_id"],
        unique=True, postgresql_where=sa.text("valid_to IS NULL"),
    )
    op.create_index("ix_item_bom_parent", "item_bom", ["parent_item_id"])
    op.create_index("ix_item_bom_component", "item_bom", ["component_item_id"])

    # 3. История изменений спецификации
    op.create_table(
        "item_change",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("old_bom_id", sa.Integer(), nullable=True),
        sa.Column("new_bom_id", sa.Integer(), nullable=True),
        sa.Column("change_type_id", sa.Integer(), nullable=False),
        sa.Column("change_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.ForeignKeyConstraint(["item_id"], ["item.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["old_bom_id"], ["item_bom.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["new_bom_id"], ["item_bom.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["change_type_id"], ["enum_value.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_item_change_item", "item_change", ["item_id"])

    # 4. Справочные перечисления
    conn = op.get_bind()
    for (type_code, type_name), values in REFERENCE_ENUMS.items():
        type_id = conn.execute(
            sa.text(
                "INSERT INTO enum_type (code, name) VALUES (:c, :n) "
                "ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name RETURNING id"
            ),
            {"c": type_code, "n": type_name},
        ).scalar_one()
        for order_number, (code, name) in enumerate(values, start=1):
            conn.execute(
                sa.text(
                    "INSERT INTO enum_value (enum_type_id, order_number, code, name) "
                    "VALUES (:t, :o, :c, :n) ON CONFLICT (enum_type_id, order_number) DO NOTHING"
                ),
                {"t": type_id, "o": order_number, "c": code, "n": name},
            )



def downgrade() -> None:
    op.drop_index("ix_item_change_item", table_name="item_change")
    op.drop_table("item_change")
    op.drop_index("ix_item_bom_component", table_name="item_bom")
    op.drop_index("ix_item_bom_parent", table_name="item_bom")
    op.drop_index("ux_item_bom_active_component", table_name="item_bom")
    op.drop_table("item_bom")
    op.drop_index("ix_item_base_item", table_name="item")
    op.drop_constraint("ck_item_not_own_base", "item", type_="check")
    op.drop_constraint("fk_item_base_item", "item", type_="foreignkey")
    op.drop_constraint("fk_item_type", "item", type_="foreignkey")
    op.drop_column("item", "base_item_id")
    op.drop_column("item", "item_type_id")
    op.execute(
        "DELETE FROM enum_type WHERE code IN ('item_type', 'bom_change_type')"
    )
