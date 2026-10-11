"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-01-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. enum_type
    op.create_table(
        "enum_type",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    # 2. unit_simple (до enum_value, т.к. enum_value.unit_id → unit_simple)
    op.create_table(
        "unit_simple",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("base_unit_id", sa.Integer(), nullable=True),
        sa.Column("coefficient", sa.Numeric(18, 6), nullable=False, server_default="1"),
        sa.Column("code", sa.String(10), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("cond_symbol_1", sa.String(20), nullable=True),
        sa.Column("cond_symbol_2", sa.String(20), nullable=True),
        sa.Column("code_symbol_1", sa.String(10), nullable=True),
        sa.Column("code_symbol_2", sa.String(10), nullable=True),
        sa.ForeignKeyConstraint(["base_unit_id"], ["unit_simple.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    # 3. enum_value (unit_id FK добавляется ниже через use_alter)
    op.create_table(
        "enum_value",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("enum_type_id", sa.Integer(), nullable=False),
        sa.Column("order_number", sa.SmallInteger(), nullable=False),
        sa.Column("code", sa.String(50), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("numeric_value", sa.Numeric(18, 6), nullable=True),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["enum_type_id"], ["enum_type.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("enum_type_id", "order_number"),
    )
    op.create_foreign_key(
        "fk_enum_value_unit", "enum_value", "unit_simple", ["unit_id"], ["id"],
        ondelete="SET NULL",
    )

    # 4. parameter
    op.create_table(
        "parameter",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("param_type_id", sa.Integer(), nullable=False),
        sa.Column("enum_type_id", sa.Integer(), nullable=True),
        sa.Column("unit_simple_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["param_type_id"], ["enum_value.id"]),
        sa.ForeignKeyConstraint(["enum_type_id"], ["enum_type.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["unit_simple_id"], ["unit_simple.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    # 5. Классификаторы
    op.create_table(
        "sxd_classifier",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["sxd_classifier.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "ho_classifier",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["ho_classifier.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "document_classifier",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["document_classifier.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "item_classifier",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("number", sa.String(50), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["item_classifier.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 6. Роли
    op.create_table(
        "sxd_role",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("inverse_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["inverse_id"], ["sxd_role.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "available_roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ho_type_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("min_count", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("max_count", sa.SmallInteger(), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["ho_type_id"], ["ho_classifier.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["sxd_role.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ho_type_id", "role_id"),
    )

    # 7. Шаблоны параметров
    op.create_table(
        "ho_class_parameter",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ho_type_id", sa.Integer(), nullable=False),
        sa.Column("parameter_id", sa.Integer(), nullable=False),
        sa.Column("display_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("min_value", sa.Numeric(18, 6), nullable=True),
        sa.Column("max_value", sa.Numeric(18, 6), nullable=True),
        sa.ForeignKeyConstraint(["ho_type_id"], ["ho_classifier.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parameter_id"], ["parameter.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ho_type_id", "parameter_id"),
    )

    op.create_table(
        "doc_class_parameter",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("doc_type_id", sa.Integer(), nullable=False),
        sa.Column("parameter_id", sa.Integer(), nullable=False),
        sa.Column("display_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("min_value", sa.Numeric(18, 6), nullable=True),
        sa.Column("max_value", sa.Numeric(18, 6), nullable=True),
        sa.ForeignKeyConstraint(["doc_type_id"], ["document_classifier.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parameter_id"], ["parameter.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("doc_type_id", "parameter_id"),
    )

    # 8. СХД
    op.create_table(
        "sxd",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sxd_class_id", sa.Integer(), nullable=True),
        sa.Column("entity_type_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("okpo", sa.String(20), nullable=True),
        sa.ForeignKeyConstraint(["sxd_class_id"], ["sxd_classifier.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["entity_type_id"], ["enum_value.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # 9. ХО и Документы
    op.create_table(
        "ho",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ho_type_id", sa.Integer(), nullable=False),
        sa.Column("document_number", sa.String(100), nullable=True),
        sa.Column("op_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=True),
        sa.ForeignKeyConstraint(["ho_type_id"], ["ho_classifier.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "document",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("doc_type_id", sa.Integer(), nullable=False),
        sa.Column("ho_id", sa.Integer(), nullable=True),
        sa.Column("reg_number", sa.String(100), nullable=True),
        sa.Column("doc_date", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["doc_type_id"], ["document_classifier.id"]),
        sa.ForeignKeyConstraint(["ho_id"], ["ho.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 10. Значения параметров
    op.create_table(
        "ho_parameter_value",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ho_id", sa.Integer(), nullable=False),
        sa.Column("ho_class_param_id", sa.Integer(), nullable=False),
        sa.Column("value_str", sa.String(500), nullable=True),
        sa.Column("value_int", sa.Integer(), nullable=True),
        sa.Column("value_real", sa.Numeric(18, 6), nullable=True),
        sa.Column("value_dt", sa.DateTime(), nullable=True),
        sa.Column("value_enum_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["ho_id"], ["ho.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ho_class_param_id"], ["ho_class_parameter.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["value_enum_id"], ["enum_value.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ho_id", "ho_class_param_id"),
    )

    op.create_table(
        "doc_parameter_value",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("doc_class_param_id", sa.Integer(), nullable=False),
        sa.Column("value_str", sa.String(500), nullable=True),
        sa.Column("value_int", sa.Integer(), nullable=True),
        sa.Column("value_real", sa.Numeric(18, 6), nullable=True),
        sa.Column("value_dt", sa.DateTime(), nullable=True),
        sa.Column("value_enum_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["document.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["doc_class_param_id"], ["doc_class_parameter.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["value_enum_id"], ["enum_value.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "doc_class_param_id"),
    )

    # 11. Роли участников в ХО
    op.create_table(
        "sxd_role_in_ho",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ho_id", sa.Integer(), nullable=False),
        sa.Column("sxd_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["ho_id"], ["ho.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sxd_id"], ["sxd.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["sxd_role.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ho_id", "sxd_id", "role_id"),
    )

    # 12. Номенклатура
    op.create_table(
        "item",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("item_class_id", sa.Integer(), nullable=True),
        sa.Column("number", sa.String(50), nullable=False),
        sa.Column("article", sa.String(100), nullable=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.ForeignKeyConstraint(["item_class_id"], ["item_classifier.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("number"),
    )

    op.create_table(
        "unit_quantity",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("unit_simple_id", sa.Integer(), nullable=False),
        sa.Column("coefficient", sa.Numeric(18, 6), nullable=False, server_default="1"),
        sa.Column("is_base", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["item_id"], ["item.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["unit_simple_id"], ["unit_simple.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("item_id", "unit_simple_id"),
    )

    op.create_table(
        "item_batch",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("quantity", sa.Numeric(18, 3), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["item.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["item_batch.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 13. Упаковка
    op.create_table(
        "packaging_type",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["packaging_type.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "packaging",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("packaging_type_id", sa.Integer(), nullable=True),
        sa.Column("weight", sa.Numeric(10, 3), nullable=True),
        sa.Column("length", sa.Numeric(10, 3), nullable=True),
        sa.Column("width", sa.Numeric(10, 3), nullable=True),
        sa.Column("height", sa.Numeric(10, 3), nullable=True),
        sa.Column("inner_volume", sa.Numeric(10, 3), nullable=True),
        sa.ForeignKeyConstraint(["packaging_type_id"], ["packaging_type.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "packaging_norm",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("packaging_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 3), nullable=False),
        sa.Column("gost_number", sa.String(50), nullable=True),
        sa.ForeignKeyConstraint(["item_id"], ["item.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["packaging_id"], ["packaging.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("item_id", "packaging_id"),
    )

    # 14. Прейскуранты и позиции
    op.create_table(
        "pricelist_set",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["parent_id"], ["pricelist_set.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "pricelist",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("pricelist_set_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("article", sa.String(100), nullable=True),
        sa.Column("price", sa.Numeric(18, 2), nullable=False),
        sa.ForeignKeyConstraint(["pricelist_set_id"], ["pricelist_set.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["item.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pricelist_set_id", "item_id"),
    )

    op.create_table(
        "position_list",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ho_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["ho_id"], ["ho.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ho_id"),
    )

    op.create_table(
        "ho_position",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("position_list_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 3), nullable=False),
        sa.Column("price", sa.Numeric(18, 2), nullable=True),
        sa.Column("unit_quantity_id", sa.Integer(), nullable=True),
        sa.Column("batch_id", sa.Integer(), nullable=True),
        sa.Column("packaging_id", sa.Integer(), nullable=True),
        sa.Column("pricelist_id", sa.Integer(), nullable=True),
        sa.Column("quantity_places", sa.Integer(), nullable=True),
        sa.Column("weight_netto", sa.Numeric(12, 3), nullable=True),
        sa.Column(
            "total_amount",
            sa.Numeric(18, 2),
            sa.Computed("quantity * COALESCE(price, 0)", persisted=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["position_list_id"], ["position_list.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["item.id"]),
        sa.ForeignKeyConstraint(["unit_quantity_id"], ["unit_quantity.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["batch_id"], ["item_batch.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["packaging_id"], ["packaging.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["pricelist_id"], ["pricelist.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("ho_position")
    op.drop_table("position_list")
    op.drop_table("pricelist")
    op.drop_table("pricelist_set")
    op.drop_table("packaging_norm")
    op.drop_table("packaging")
    op.drop_table("packaging_type")
    op.drop_table("item_batch")
    op.drop_table("unit_quantity")
    op.drop_table("item")
    op.drop_table("sxd_role_in_ho")
    op.drop_table("doc_parameter_value")
    op.drop_table("ho_parameter_value")
    op.drop_table("document")
    op.drop_table("ho")
    op.drop_table("sxd")
    op.drop_table("doc_class_parameter")
    op.drop_table("ho_class_parameter")
    op.drop_table("available_roles")
    op.drop_table("sxd_role")
    op.drop_table("item_classifier")
    op.drop_table("document_classifier")
    op.drop_table("ho_classifier")
    op.drop_table("sxd_classifier")
    op.drop_table("parameter")
    op.drop_constraint("fk_enum_value_unit", "enum_value", type_="foreignkey")
    op.drop_table("enum_value")
    op.drop_table("unit_simple")
    op.drop_table("enum_type")
