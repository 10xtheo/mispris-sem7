from sqlalchemy import inspect, text
from src.repository.rule_repository import RuleRepository
from src.models.configuration import ConfigurationFunction
from src.models.rule_structure import RuleExpression, RuleFormalArgument, RuleActualArgument
from tests.e2e.test_lab7_scenarios import configurator  # noqa: F401
from tests.unit.test_constraint_interpreter import const, op, param


def test_functions_are_read_from_relational_entities(client,session,configurator):
    definition={"parameters":{"x":"number"},"result":"bool","body":op("ge",param("x"),const(30))}
    response=client.post("/api/configuration/functions",json={"code":"Relational","name":"Проверка","definition":definition})
    assert response.status_code==201
    repo=RuleRepository(session)
    row=repo.rows(ConfigurationFunction,code="Relational")[0]
    assert repo.definition(row.id)==definition
    assert repo.rows(RuleFormalArgument,function_id=row.id)
    assert len(repo.rows(RuleActualArgument))==2
    assert "definition" not in {c["name"] for c in inspect(session.connection()).get_columns("configuration_function")}
    assert "expression" not in {c["name"] for c in inspect(session.connection()).get_columns("configuration_constraint")}
