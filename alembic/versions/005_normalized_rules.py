"""Нормализованное хранение функций, вызовов и аргументов задания №7."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Session

revision="005"
down_revision="004"
branch_labels=None
depends_on=None
NAMES=("rule_function_class","rule_operator","rule_formal_argument","rule_constant",
       "rule_expression","rule_actual_argument","rule_function_definition","rule_constraint_root")


DDL = ['\nCREATE TABLE rule_function_class (\n\tid SERIAL NOT NULL, \n\tcode VARCHAR(50) NOT NULL, \n\tname VARCHAR(255) NOT NULL, \n\tparent_id INTEGER, \n\tPRIMARY KEY (id), \n\tUNIQUE (code), \n\tFOREIGN KEY(parent_id) REFERENCES rule_function_class (id)\n)\n\n', '\nCREATE TABLE rule_operator (\n\tid SERIAL NOT NULL, \n\tcode VARCHAR(20) NOT NULL, \n\tclass_id INTEGER NOT NULL, \n\tresult_type VARCHAR(20) NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (code), \n\tFOREIGN KEY(class_id) REFERENCES rule_function_class (id)\n)\n\n', '\nCREATE TABLE rule_formal_argument (\n\tfunction_id INTEGER NOT NULL, \n\tnumber INTEGER NOT NULL, \n\tname VARCHAR(100) NOT NULL, \n\tvalue_type VARCHAR(20) NOT NULL, \n\tPRIMARY KEY (function_id, number), \n\tUNIQUE (function_id, name), \n\tCONSTRAINT ck_rule_formal_number CHECK (number > 0), \n\tFOREIGN KEY(function_id) REFERENCES configuration_function (id)\n)\n\n', "\nCREATE TABLE rule_constant (\n\tid SERIAL NOT NULL, \n\tvalue_type VARCHAR(20) NOT NULL, \n\tvalue_text VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT ck_rule_constant_type CHECK (value_type IN ('number','string','bool'))\n)\n\n", "\nCREATE TABLE rule_expression (\n\tid SERIAL NOT NULL, \n\tkind VARCHAR(20) NOT NULL, \n\tfunction_id INTEGER, \n\toperator_id INTEGER, \n\tconstant_id INTEGER, \n\tparameter_name VARCHAR(100), \n\tPRIMARY KEY (id), \n\tCONSTRAINT ck_rule_expression_kind CHECK ((kind='call' AND function_id IS NOT NULL AND operator_id IS NULL AND constant_id IS NULL AND parameter_name IS NULL) OR (kind='op' AND function_id IS NULL AND operator_id IS NOT NULL AND constant_id IS NULL AND parameter_name IS NULL) OR (kind='const' AND function_id IS NULL AND operator_id IS NULL AND constant_id IS NOT NULL AND parameter_name IS NULL) OR (kind='param' AND function_id IS NULL AND operator_id IS NULL AND constant_id IS NULL AND parameter_name IS NOT NULL)), \n\tFOREIGN KEY(function_id) REFERENCES configuration_function (id), \n\tFOREIGN KEY(operator_id) REFERENCES rule_operator (id), \n\tFOREIGN KEY(constant_id) REFERENCES rule_constant (id)\n)\n\n", '\nCREATE TABLE rule_actual_argument (\n\texpression_id INTEGER NOT NULL, \n\tnumber INTEGER NOT NULL, \n\tname VARCHAR(100), \n\tvalue_expression_id INTEGER NOT NULL, \n\tPRIMARY KEY (expression_id, number), \n\tUNIQUE (expression_id, name), \n\tCONSTRAINT ck_rule_actual_number CHECK (number > 0), \n\tFOREIGN KEY(expression_id) REFERENCES rule_expression (id), \n\tFOREIGN KEY(value_expression_id) REFERENCES rule_expression (id)\n)\n\n', '\nCREATE TABLE rule_function_definition (\n\tfunction_id INTEGER NOT NULL, \n\tclass_id INTEGER NOT NULL, \n\tresult_type VARCHAR(20) NOT NULL, \n\tbody_id INTEGER NOT NULL, \n\tPRIMARY KEY (function_id), \n\tFOREIGN KEY(function_id) REFERENCES configuration_function (id), \n\tFOREIGN KEY(class_id) REFERENCES rule_function_class (id), \n\tFOREIGN KEY(body_id) REFERENCES rule_expression (id)\n)\n\n', '\nCREATE TABLE rule_constraint_root (\n\tconstraint_id INTEGER NOT NULL, \n\texpression_id INTEGER NOT NULL, \n\tPRIMARY KEY (constraint_id), \n\tFOREIGN KEY(constraint_id) REFERENCES configuration_constraint (id), \n\tFOREIGN KEY(expression_id) REFERENCES rule_expression (id)\n)\n\n']

def upgrade():
    from sqlmodel import SQLModel
    import src.models
    from src.models.rule_structure import RuleFunctionClass,RuleOperator
    from src.repository.rule_repository import RuleRepository
    bind=op.get_bind()
    functions=bind.execute(sa.text("SELECT id, definition FROM configuration_function")).all()
    rules=bind.execute(sa.text("SELECT id, expression FROM configuration_constraint")).all()
    for statement in DDL: op.execute(statement)
    with Session(bind=bind,join_transaction_mode="create_savepoint") as session:
        repo=RuleRepository(session)
        classes={code:repo.save(RuleFunctionClass(code=code,name=name)).id for code,name in (
            ("arithmetic","Арифметические функции"),("predicate","Предикаты"),
            ("logical","Логические функции"),("composed","Составные функции"))}
        for code in ("+","-","*","/","eq","ne","gt","ge","lt","le","in","and","or","not"):
            kind="arithmetic" if code in ("+","-","*","/") else "logical" if code in ("and","or","not") else "predicate"
            repo.save(RuleOperator(code=code,class_id=classes[kind],result_type="number" if kind=="arithmetic" else "bool"))
        for key,definition in functions: repo.store_function(key,definition)
        for key,expression in rules: repo.store_constraint(key,expression)
        session.commit()
    op.drop_column("configuration_function","definition")
    op.drop_column("configuration_constraint","expression")


def downgrade():
    import json
    from decimal import Decimal
    from src.repository.rule_repository import RuleRepository
    from src.models.configuration import ConfigurationFunction,ConfigurationConstraint
    bind=op.get_bind()
    op.add_column("configuration_function",sa.Column("definition",JSONB,nullable=False,server_default="{}"))
    op.add_column("configuration_constraint",sa.Column("expression",JSONB,nullable=False,server_default="{}"))
    with Session(bind=bind,join_transaction_mode="create_savepoint") as session:
        repo=RuleRepository(session)
        for model,column,reader in ((ConfigurationFunction,"definition",repo.definition),(ConfigurationConstraint,"expression",repo.constraint)):
            for row in repo.rows(model):
                payload=json.dumps(reader(row.id),default=lambda v:float(v) if isinstance(v,Decimal) else v)
                bind.execute(sa.text(f"UPDATE {model.__tablename__} SET {column}=CAST(:data AS jsonb) WHERE id=:id"),dict(data=payload,id=row.id))
        session.commit()
    for name in reversed(NAMES): op.drop_table(name)
