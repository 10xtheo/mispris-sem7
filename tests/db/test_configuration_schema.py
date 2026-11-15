from sqlalchemy import inspect
from sqlmodel import SQLModel


TABLES = ("item_configuration", "class_configuration_parameter", "variant_parameter_value",
          "configuration_function", "configuration_constraint", "customer_order", "customer_order_position",
          "rule_function_class","rule_operator","rule_formal_argument","rule_constant",
          "rule_expression","rule_actual_argument","rule_function_definition","rule_constraint_root")


def test_lab7_keys_checks_and_uniques_match_models(session):
    inspector = inspect(session.connection())
    for name in TABLES:
        table = SQLModel.metadata.tables[name]
        assert {col["name"] for col in inspector.get_columns(name)} == set(table.columns.keys())
        expected_fk = {(tuple(c.parent.name for c in fk.elements),
                        fk.elements[0].column.table.name, tuple(c.column.name for c in fk.elements))
                       for fk in table.foreign_key_constraints}
        actual_fk = {(tuple(fk["constrained_columns"]), fk["referred_table"], tuple(fk["referred_columns"]))
                     for fk in inspector.get_foreign_keys(name)}
        assert expected_fk == actual_fk, name
        from sqlalchemy import CheckConstraint, UniqueConstraint
        assert {constraint.name for constraint in table.constraints if isinstance(constraint, CheckConstraint)} == {
            row["name"] for row in inspector.get_check_constraints(name)}
        assert {tuple(col.name for col in constraint.columns) for constraint in table.constraints
                if isinstance(constraint, UniqueConstraint)} == {
            tuple(row["column_names"]) for row in inspector.get_unique_constraints(name)}
