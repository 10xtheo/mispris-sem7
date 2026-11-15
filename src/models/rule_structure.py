"""Нормализованные сущности ограничений задания №7, слайды 15–18."""
from typing import ClassVar, Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import CheckConstraint, UniqueConstraint


class RuleFunctionClass(SQLModel, table=True):
    __tablename__: ClassVar[str] = "rule_function_class"
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(max_length=50, unique=True)
    name: str = Field(max_length=255)
    parent_id: Optional[int] = Field(default=None, foreign_key="rule_function_class.id")


class RuleOperator(SQLModel, table=True):
    __tablename__: ClassVar[str] = "rule_operator"
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(max_length=20, unique=True)
    class_id: int = Field(foreign_key="rule_function_class.id")
    result_type: str = Field(max_length=20)


class RuleFormalArgument(SQLModel, table=True):
    __tablename__: ClassVar[str] = "rule_formal_argument"
    __table_args__ = (UniqueConstraint("function_id", "name"), CheckConstraint("number > 0", name="ck_rule_formal_number"),)
    function_id: int = Field(primary_key=True, foreign_key="configuration_function.id")
    number: int = Field(primary_key=True)
    name: str = Field(max_length=100)
    value_type: str = Field(max_length=20)


class RuleConstant(SQLModel, table=True):
    __tablename__: ClassVar[str] = "rule_constant"
    __table_args__ = (CheckConstraint("value_type IN ('number','string','bool')", name="ck_rule_constant_type"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    value_type: str = Field(max_length=20)
    value_text: str


class RuleExpression(SQLModel, table=True):
    """FACT_FUN для call; также узлы операторов, констант и параметров."""
    __tablename__: ClassVar[str] = "rule_expression"
    __table_args__ = (CheckConstraint(
        "(kind='call' AND function_id IS NOT NULL AND operator_id IS NULL AND constant_id IS NULL AND parameter_name IS NULL) OR "
        "(kind='op' AND function_id IS NULL AND operator_id IS NOT NULL AND constant_id IS NULL AND parameter_name IS NULL) OR "
        "(kind='const' AND function_id IS NULL AND operator_id IS NULL AND constant_id IS NOT NULL AND parameter_name IS NULL) OR "
        "(kind='param' AND function_id IS NULL AND operator_id IS NULL AND constant_id IS NULL AND parameter_name IS NOT NULL)", name="ck_rule_expression_kind"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    kind: str = Field(max_length=20)
    function_id: Optional[int] = Field(default=None, foreign_key="configuration_function.id")
    operator_id: Optional[int] = Field(default=None, foreign_key="rule_operator.id")
    constant_id: Optional[int] = Field(default=None, foreign_key="rule_constant.id")
    parameter_name: Optional[str] = Field(default=None, max_length=100)


class RuleActualArgument(SQLModel, table=True):
    """FACT_PAR: позиция и имя аргумента, ссылка на выражение-значение."""
    __tablename__: ClassVar[str] = "rule_actual_argument"
    __table_args__ = (UniqueConstraint("expression_id", "name"), CheckConstraint("number > 0", name="ck_rule_actual_number"),)
    expression_id: int = Field(primary_key=True, foreign_key="rule_expression.id")
    number: int = Field(primary_key=True)
    name: Optional[str] = Field(default=None, max_length=100)
    value_expression_id: int = Field(foreign_key="rule_expression.id")


class RuleFunctionDefinition(SQLModel, table=True):
    __tablename__: ClassVar[str] = "rule_function_definition"
    function_id: int = Field(primary_key=True, foreign_key="configuration_function.id")
    class_id: int = Field(foreign_key="rule_function_class.id")
    result_type: str = Field(max_length=20)
    body_id: int = Field(foreign_key="rule_expression.id")


class RuleConstraintRoot(SQLModel, table=True):
    __tablename__: ClassVar[str] = "rule_constraint_root"
    constraint_id: int = Field(primary_key=True, foreign_key="configuration_constraint.id")
    expression_id: int = Field(foreign_key="rule_expression.id")
