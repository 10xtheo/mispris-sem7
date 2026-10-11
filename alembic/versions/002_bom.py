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


# --------------------------------------------------------------------------
# SQL-функции бизнес-логики
# --------------------------------------------------------------------------
FUNCTIONS_SQL = r"""
-- Действующая спецификация изделия на момент p_at (один уровень).
-- Для модификации: собственные строки + строки базовой спецификации
-- (is_base) базовых изделий по цепочке base_item_id, если компонент
-- не переопределён и не исключён (is_excluded) ближе по цепочке.
CREATE OR REPLACE FUNCTION effective_bom(
    p_item_id integer,
    p_at timestamptz,
    p_include_excluded boolean DEFAULT false
) RETURNS TABLE (
    bom_id integer,
    owner_item_id integer,
    inherit_level integer,
    component_item_id integer,
    quantity numeric,
    for_quantity numeric,
    unit_quantity_id integer,
    is_base boolean,
    is_excluded boolean,
    order_number integer
) LANGUAGE sql STABLE AS $$
    WITH RECURSIVE chain(item_id, lvl) AS (
        SELECT p_item_id, 0
        UNION ALL
        SELECT i.base_item_id, c.lvl + 1
        FROM chain c
        JOIN item i ON i.id = c.item_id
        WHERE i.base_item_id IS NOT NULL AND c.lvl < 32
    ),
    candidates AS (
        SELECT DISTINCT ON (b.component_item_id)
               b.id, b.parent_item_id, c.lvl, b.component_item_id,
               b.quantity, b.for_quantity, b.unit_quantity_id,
               b.is_base, b.is_excluded, b.order_number
        FROM item_bom b
        JOIN chain c ON c.item_id = b.parent_item_id
        WHERE b.valid_from <= p_at
          AND (b.valid_to IS NULL OR b.valid_to > p_at)
          AND (c.lvl = 0 OR b.is_base)
        ORDER BY b.component_item_id, c.lvl
    )
    SELECT * FROM candidates c
    WHERE p_include_excluded OR NOT c.is_excluded
    ORDER BY c.order_number, c.component_item_id;
$$;

-- FIND_BOM: полный состав изделия на всю глубину вложенности.
-- norm — расход компонента в его базовой ЕИ на 1 базовую ЕИ корневого изделия.
-- is_cycle — защита от зацикливания (компонент уже встречался на пути).
CREATE OR REPLACE FUNCTION find_bom(p_item_id integer, p_at timestamptz)
RETURNS TABLE (
    lvl integer,
    sort_path integer[],
    path integer[],
    parent_item_id integer,
    component_item_id integer,
    bom_id integer,
    owner_item_id integer,
    inherited boolean,
    quantity numeric,
    for_quantity numeric,
    unit_quantity_id integer,
    coefficient numeric,
    qty_base numeric,
    norm numeric,
    is_cycle boolean
) LANGUAGE sql STABLE AS $$
    WITH RECURSIVE tree AS (
        SELECT 1 AS lvl,
               ARRAY[e.order_number, e.component_item_id] AS sort_path,
               ARRAY[p_item_id, e.component_item_id] AS path,
               p_item_id AS parent_item_id,
               e.component_item_id,
               e.bom_id,
               e.owner_item_id,
               (e.owner_item_id <> p_item_id) AS inherited,
               e.quantity,
               e.for_quantity,
               e.unit_quantity_id,
               COALESCE(uq.coefficient, 1)::numeric AS coefficient,
               (e.quantity * COALESCE(uq.coefficient, 1))::numeric AS qty_base,
               (e.quantity * COALESCE(uq.coefficient, 1) / e.for_quantity)::numeric AS norm,
               false AS is_cycle
        FROM effective_bom(p_item_id, p_at) e
        LEFT JOIN unit_quantity uq ON uq.id = e.unit_quantity_id
        UNION ALL
        SELECT t.lvl + 1,
               t.sort_path || ARRAY[e.order_number, e.component_item_id],
               t.path || e.component_item_id,
               t.component_item_id,
               e.component_item_id,
               e.bom_id,
               e.owner_item_id,
               (e.owner_item_id <> t.component_item_id),
               e.quantity,
               e.for_quantity,
               e.unit_quantity_id,
               COALESCE(uq.coefficient, 1)::numeric,
               (e.quantity * COALESCE(uq.coefficient, 1))::numeric,
               (t.norm * e.quantity * COALESCE(uq.coefficient, 1) / e.for_quantity)::numeric,
               e.component_item_id = ANY(t.path)
        FROM tree t
        CROSS JOIN LATERAL effective_bom(t.component_item_id, p_at) e
        LEFT JOIN unit_quantity uq ON uq.id = e.unit_quantity_id
        WHERE NOT t.is_cycle AND t.lvl < 100
    )
    SELECT tree.lvl, tree.sort_path, tree.path, tree.parent_item_id, tree.component_item_id,
           tree.bom_id, tree.owner_item_id, tree.inherited, tree.quantity, tree.for_quantity,
           tree.unit_quantity_id, tree.coefficient, tree.qty_base, tree.norm, tree.is_cycle
    FROM tree
    ORDER BY tree.sort_path;
$$;

-- CALC_BOM: сводные нормы расхода на p_qty единиц изделия.
-- p_class_id IS NULL  — по всем материальным ресурсам (листьям дерева состава);
-- p_class_id задан    — по компонентам этого класса и его подклассов; на каждом
--                       пути берётся первый найденный компонент класса (без
--                       двойного счёта вложенных компонентов того же класса).
CREATE OR REPLACE FUNCTION calc_bom(
    p_item_id integer,
    p_qty numeric,
    p_class_id integer,
    p_at timestamptz
) RETURNS TABLE (component_item_id integer, total_quantity numeric)
LANGUAGE sql STABLE AS $$
    WITH RECURSIVE class_tree(id) AS (
        SELECT p_class_id WHERE p_class_id IS NOT NULL
        UNION ALL
        SELECT ic.id FROM item_classifier ic JOIN class_tree ct ON ic.parent_id = ct.id
    ),
    tree AS (
        SELECT f.* FROM find_bom(p_item_id, p_at) f WHERE NOT f.is_cycle
    )
    SELECT t.component_item_id, SUM(t.norm) * p_qty
    FROM tree t
    JOIN item i ON i.id = t.component_item_id
    WHERE (
        p_class_id IS NULL
        AND NOT EXISTS (SELECT 1 FROM effective_bom(t.component_item_id, p_at))
    ) OR (
        p_class_id IS NOT NULL
        AND i.item_class_id IN (SELECT id FROM class_tree)
        AND NOT EXISTS (
            SELECT 1
            FROM unnest(t.path[2:t.lvl]) AS anc(id)
            JOIN item ai ON ai.id = anc.id
            WHERE ai.item_class_id IN (SELECT id FROM class_tree)
        )
    )
    GROUP BY t.component_item_id;
$$;

-- Проверка цикла в составе изделия и всех его модификаций
-- (модификации наследуют базовую спецификацию, поэтому цикл может пройти через них).
CREATE OR REPLACE FUNCTION bom_has_cycle(p_item_id integer, p_at timestamptz)
RETURNS boolean LANGUAGE sql STABLE AS $$
    WITH RECURSIVE affected(id) AS (
        SELECT p_item_id
        UNION
        SELECT i.id FROM item i JOIN affected a ON i.base_item_id = a.id
    )
    SELECT EXISTS (
        SELECT 1
        FROM affected a
        CROSS JOIN LATERAL find_bom(a.id, p_at) f
        WHERE f.is_cycle
    );
$$;
"""

DROP_FUNCTIONS_SQL = """
DROP FUNCTION IF EXISTS bom_has_cycle(integer, timestamptz);
DROP FUNCTION IF EXISTS calc_bom(integer, numeric, integer, timestamptz);
DROP FUNCTION IF EXISTS find_bom(integer, timestamptz);
DROP FUNCTION IF EXISTS effective_bom(integer, timestamptz, boolean);
"""


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
        sa.ForeignKeyConstraint(["unit_quantity_id"], ["unit_quantity.id"], ondelete="SET NULL"),
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

    # 5. Функции FIND_BOM / CALC_BOM и вспомогательные
    op.execute(FUNCTIONS_SQL)


def downgrade() -> None:
    op.execute(DROP_FUNCTIONS_SQL)
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
