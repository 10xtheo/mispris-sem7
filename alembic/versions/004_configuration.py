"""№7: заказы с вариантами исполнения и интерпретируемые ограничения."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def ref(name, target, *, primary_key=False, nullable=False):
    return sa.Column(name, sa.Integer, sa.ForeignKey(target), primary_key=primary_key, nullable=nullable)


def identifier():
    return sa.Column("id", sa.Integer, primary_key=True)


def upgrade():
    op.create_table("item_configuration",
        ref("item_id", "item.id", primary_key=True), sa.Column("kind", sa.String(20), nullable=False),
        ref("template_id", "item.id", nullable=True),
        sa.CheckConstraint("(kind = 'template' AND template_id IS NULL) OR (kind = 'variant' AND template_id IS NOT NULL AND template_id <> item_id)", name="ck_item_configuration_kind"))
    op.create_table("class_configuration_parameter", identifier(), ref("class_id", "item_classifier.id"),
        ref("parameter_id", "parameter.id"), sa.Column("flag_conf", sa.Boolean, nullable=False),
        sa.Column("required", sa.Boolean, nullable=False), sa.Column("display_order", sa.Integer, nullable=False),
        sa.Column("min_value", sa.Numeric(18, 6)), sa.Column("max_value", sa.Numeric(18, 6)),
        sa.UniqueConstraint("class_id", "parameter_id"),
        sa.CheckConstraint("min_value IS NULL OR max_value IS NULL OR min_value <= max_value", name="ck_configuration_range"))
    op.create_table("variant_parameter_value", ref("item_id", "item.id", primary_key=True),
        ref("parameter_id", "parameter.id", primary_key=True), sa.Column("value", JSONB, nullable=False))
    op.create_table("configuration_function", identifier(), sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False), sa.Column("definition", JSONB, nullable=False))
    op.create_table("configuration_constraint", identifier(), ref("template_id", "item.id"),
        sa.Column("name", sa.String(255), nullable=False), sa.Column("expression", JSONB, nullable=False),
        sa.UniqueConstraint("template_id", "name"))
    op.create_table("customer_order", identifier(), sa.Column("number", sa.String(50), nullable=False, unique=True),
        sa.Column("customer", sa.String(255), nullable=False), sa.Column("order_date", sa.Date, nullable=False),
        sa.Column("status", sa.String(20), nullable=False), ref("ho_id", "ho.id", nullable=True),
        sa.CheckConstraint("status IN ('draft', 'agreed')", name="ck_customer_order_status"))
    op.create_table("customer_order_position", identifier(), ref("order_id", "customer_order.id"),
        sa.Column("number", sa.Integer, nullable=False), ref("item_id", "item.id"),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=False), sa.UniqueConstraint("order_id", "number"),
        sa.CheckConstraint("quantity > 0 AND number > 0", name="ck_order_position_quantity"))


def downgrade():
    for table in ("customer_order_position", "customer_order", "configuration_constraint", "configuration_function",
                  "variant_parameter_value", "class_configuration_parameter", "item_configuration"):
        op.drop_table(table)
