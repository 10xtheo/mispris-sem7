"""EVAL_FUNCTION: типизированный интерпретатор функций ограничений №7.

Узлы: const/value, param/name, call/function/args, op/args.
Функция: parameters={имя: number|string|bool}, result=тип, body=узел.
Фактические аргументы вызова сами являются выражениями. Python-код не исполняется.
"""
from decimal import Decimal, InvalidOperation, localcontext

from src.core.errors import BusinessRuleError


class ConstraintInterpreter:
    MAX_DEPTH = 40
    MAX_NODES = 2000

    def __init__(self, functions):
        self.functions = functions

    @staticmethod
    def typed(value, expected):
        if expected == "bool" and type(value) is bool:
            return value
        if expected == "string" and type(value) is str:
            return value
        if expected == "number" and type(value) in (int, float, Decimal):
            result = Decimal(str(value))
            if result.is_finite():
                return result
        raise BusinessRuleError(f"Ожидался тип {expected}")

    def evaluate(self, expression, values):
        """EVAL_FUNCTION: вычисление дерева с ограничением глубины и объёма."""
        self.remaining = self.MAX_NODES
        try:
            with localcontext() as context:
                context.prec = 28
                return self._eval(expression, values, (), 0)
        except (InvalidOperation, OverflowError, ZeroDivisionError) as exc:
            raise BusinessRuleError("Недопустимое арифметическое действие") from exc

    def validate(self, expression, parameters):
        """Проверка структуры и типов всех ветвей до сохранения правила."""
        self.remaining = self.MAX_NODES
        return self._validate(expression, parameters, (), 0)

    def _validate(self, node, parameters, stack, depth):
        self.remaining -= 1
        if depth > self.MAX_DEPTH or self.remaining < 0:
            raise BusinessRuleError("Превышена сложность выражения")
        if not isinstance(node, dict):
            raise BusinessRuleError("Ожидался узел выражения")
        kind = node.get("kind")
        if kind == "const" and set(node) == {"kind", "value"}:
            value = node["value"]
            typ = "bool" if type(value) is bool else "string" if type(value) is str else "number"
            self.typed(value, typ)
            return typ
        if kind == "param" and set(node) == {"kind", "name"}:
            name = node["name"]
            if not isinstance(name, str) or name not in parameters:
                raise BusinessRuleError("Неизвестный параметр выражения")
            return parameters[name]
        if kind == "call" and set(node) == {"kind", "function", "args"}:
            name, args = node["function"], node["args"]
            if not isinstance(name, str) or not isinstance(args, dict) or name not in self.functions:
                raise BusinessRuleError("Неизвестная функция или неверный вызов")
            if name in stack:
                raise BusinessRuleError("Цикл вызовов функций")
            definition = self.functions[name]
            formal = definition["parameters"]
            if set(formal) != set(args):
                raise BusinessRuleError("Аргументы не соответствуют сигнатуре")
            for key, typ in formal.items():
                if self._validate(args[key], parameters, stack, depth + 1) != typ:
                    raise BusinessRuleError("Тип фактического аргумента не соответствует формальному")
            result = self._validate(definition["body"], formal, stack + (name,), depth + 1)
            if result != definition["result"]:
                raise BusinessRuleError("Тип результата функции не соответствует объявленному")
            return result
        if kind != "op" or set(node) != {"kind", "op", "args"}:
            raise BusinessRuleError("Неизвестный или некорректный узел выражения")
        op, args = node["op"], node["args"]
        if not isinstance(op, str) or not isinstance(args, list):
            raise BusinessRuleError("Некорректные аргументы оператора")
        arities = {"not": (1, 1), "and": (2, 50), "or": (2, 50), "in": (2, 50)}
        supported = {"not", "and", "or", "in", "+", "-", "*", "/", "eq", "ne", "gt", "ge", "lt", "le"}
        lo, hi = arities.get(op, (2, 2))
        if op not in supported or not lo <= len(args) <= hi:
            raise BusinessRuleError("Неизвестный оператор или число аргументов")
        types = [self._validate(arg, parameters, stack, depth + 1) for arg in args]
        expected = "bool" if op in ("not", "and", "or") else "number"
        if op in ("eq", "ne", "in"):
            if len(set(types)) != 1:
                raise BusinessRuleError("Типы сравниваемых аргументов различаются")
        elif any(typ != expected for typ in types):
            raise BusinessRuleError(f"Оператор {op} требует тип {expected}")
        return "number" if op in ("+", "-", "*", "/") else "bool"

    def _eval(self, node, values, stack, depth):
        self.remaining -= 1
        if depth > self.MAX_DEPTH or self.remaining < 0:
            raise BusinessRuleError("Превышена сложность выражения")
        if not isinstance(node, dict):
            raise BusinessRuleError("Ожидался узел выражения")
        kind = node.get("kind")
        if kind == "const" and set(node) == {"kind", "value"}:
            value = node["value"]
            if type(value) in (str, bool):
                return value
            return self.typed(value, "number")
        if kind == "param" and set(node) == {"kind", "name"}:
            if not isinstance(node["name"], str):
                raise BusinessRuleError("Имя параметра должно быть строкой")
            if node["name"] not in values:
                raise BusinessRuleError(f"Не задан параметр {node['name']}")
            return values[node["name"]]
        if kind == "call" and set(node) == {"kind", "function", "args"}:
            name, args = node["function"], node["args"]
            if not isinstance(name, str) or not isinstance(args, dict):
                raise BusinessRuleError("Некорректный вызов функции")
            if name in stack:
                raise BusinessRuleError("Цикл вызовов функций")
            definition = self.functions.get(name)
            if not definition:
                raise BusinessRuleError(f"Функция {name} не найдена")
            formal = definition["parameters"]
            if set(formal) != set(args):
                raise BusinessRuleError(f"Аргументы функции {name} не соответствуют сигнатуре")
            actual = {key: self.typed(self._eval(args[key], values, stack, depth + 1), typ)
                      for key, typ in formal.items()}
            result = self._eval(definition["body"], actual, stack + (name,), depth + 1)
            return self.typed(result, definition["result"])
        if kind != "op" or set(node) != {"kind", "op", "args"}:
            raise BusinessRuleError("Неизвестный или некорректный узел выражения")
        op, args = node["op"], node["args"]
        if not isinstance(args, list) or not isinstance(op, str):
            raise BusinessRuleError("Некорректные аргументы оператора")
        arities = {"not": (1, 1), "and": (2, 50), "or": (2, 50), "in": (2, 50)}
        lo, hi = arities.get(op, (2, 2))
        if not lo <= len(args) <= hi:
            raise BusinessRuleError(f"Неверное число аргументов {op}")
        vals = [self._eval(arg, values, stack, depth + 1) for arg in args]
        if op in ("and", "or", "not"):
            vals = [self.typed(v, "bool") for v in vals]
            return all(vals) if op == "and" else any(vals) if op == "or" else not vals[0]
        if op in ("+", "-", "*", "/"):
            a, b = [self.typed(v, "number") for v in vals]
            if op == "/" and b == 0:
                raise BusinessRuleError("Деление на ноль")
            result = {"+": lambda: a + b, "-": lambda: a - b,
                      "*": lambda: a * b, "/": lambda: a / b}[op]()
            if not result.is_finite() or abs(result) > Decimal("1e30"):
                raise BusinessRuleError("Результат выходит за допустимый диапазон")
            return result
        # bool не считается числом; Python иначе считает True == 1.
        types = {type(v) for v in vals}
        if len(types) != 1:
            raise BusinessRuleError("Типы сравниваемых аргументов различаются")
        if op == "in":
            return vals[0] in vals[1:]
        a, b = vals
        if op in ("eq", "ne"):
            return a == b if op == "eq" else a != b
        if op in ("gt", "ge", "lt", "le"):
            a, b = [self.typed(v, "number") for v in vals]
            return {"gt": a > b, "ge": a >= b, "lt": a < b, "le": a <= b}[op]
        raise BusinessRuleError(f"Неизвестный оператор {op}")
