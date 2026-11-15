from decimal import Decimal

import pytest

from src.core.errors import BusinessRuleError
from src.services.constraint_interpreter import ConstraintInterpreter


def const(value):
    return {"kind": "const", "value": value}


def param(name):
    return {"kind": "param", "name": name}


def op(name, *args):
    return {"kind": "op", "op": name, "args": list(args)}


def call(name, **args):
    return {"kind": "call", "function": name, "args": args}


def test_nested_function_formal_and_actual_arguments():
    ratio = op("/", param("h"), param("w"))
    functions = {"ratio": {"parameters": {"h": "number", "w": "number"},
                            "result": "number", "body": ratio}}
    invocation = call("ratio", h=param("height"), w=const(200))
    rule = op("and", op("ge", invocation, const(0.5)), op("le", invocation, const(2)))
    engine = ConstraintInterpreter(functions)
    assert engine.evaluate(rule, {"height": Decimal(100)}) is True
    assert engine.evaluate(rule, {"height": Decimal(401)}) is False


@pytest.mark.parametrize("expression", [
    op("/", const(1), const(0)), op("eq", const(True), const(1)),
    op("+", const("1"), const(1)), op("not", const(1)),
    param("missing"), op("exec", const(1), const(2)),
    call("missing"), {"kind": "const", "value": None},
    op("eq", const(1)), {"kind": "const", "value": 1, "code": "danger"},
])
def test_invalid_expression_has_domain_error(expression):
    with pytest.raises(BusinessRuleError):
        ConstraintInterpreter({}).evaluate(expression, {})


def test_cycle_and_wrong_signature():
    definition = {"parameters": {}, "result": "bool", "body": call("self")}
    with pytest.raises(BusinessRuleError, match="Цикл"):
        ConstraintInterpreter({"self": definition}).evaluate(call("self"), {})
    with pytest.raises(BusinessRuleError, match="сигнатуре"):
        ConstraintInterpreter({"self": definition}).evaluate(call("self", x=const(1)), {})


def test_membership_and_logic():
    engine = ConstraintInterpreter({})
    assert engine.evaluate(op("in", param("base"), const("thin"), const("thick")), {"base": "thin"})
    assert not engine.evaluate(op("not", const(True)), {})
    assert engine.evaluate(op("or", const(False), const(True)), {})


def test_excessive_depth_is_rejected():
    expression = const(True)
    for _ in range(50):
        expression = op("not", expression)
    with pytest.raises(BusinessRuleError, match="сложность"):
        ConstraintInterpreter({}).evaluate(expression, {})
