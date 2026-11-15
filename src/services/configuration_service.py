from decimal import Decimal

from src.core.errors import BusinessRuleError, ConflictError, NotFoundError
from src.models.classifiers import ItemClassifier
from src.models.configuration import (
    ClassConfigurationParameter, ConfigurationConstraint, ConfigurationFunction,
    CustomerOrder, CustomerOrderPosition, ItemConfiguration, VariantParameterValue,
)
from src.models.enums import EnumType, EnumValue
from src.models.ho import Ho
from src.models.items import Item, UnitQuantity
from src.models.parameters import Parameter
from src.models.units import UnitSimple
from src.services.constraint_interpreter import ConstraintInterpreter


class ConfigurationService:
    def __init__(self, repo):
        self.repo = repo

    def require(self, model, key):
        row = self.repo.get(model, key)
        if row is None:
            raise NotFoundError(f"{model.__tablename__}: запись {key} не найдена")
        return row

    def template(self, item_id):
        item = self.require(Item, item_id)
        meta = self.repo.get(ItemConfiguration, item_id)
        if not meta or meta.kind != "template":
            raise BusinessRuleError("Изделие не является типовым с конфигуратором")
        return item

    def enable_template(self, item_id):
        self.repo.lock()
        item = self.require(Item, item_id)
        if item.item_class_id is None:
            raise BusinessRuleError("Для конфигуратора необходим класс изделия")
        if self.repo.rows(CustomerOrderPosition, item_id=item_id):
            raise ConflictError("Изделие уже используется в заказе")
        meta = self.repo.get(ItemConfiguration, item_id)
        if meta and meta.kind == "variant":
            raise BusinessRuleError("Вариант не может быть шаблоном")
        return meta or self.repo.save(ItemConfiguration(item_id=item_id, kind="template"))

    def assign_parameter(self, class_id, data):
        self.repo.lock()
        self.require(ItemClassifier, class_id)
        self.ensure_class_mutable(class_id)
        parameter = self.require(Parameter, data.parameter_id)
        self.parameter_type(parameter)
        existing = self.repo.rows(ClassConfigurationParameter, class_id=class_id, parameter_id=data.parameter_id)
        if existing:
            raise ConflictError("Параметр уже назначен этому классу")
        return self.repo.save(ClassConfigurationParameter(class_id=class_id, **data.model_dump()))

    def parameter_type(self, parameter):
        value = self.require(EnumValue, parameter.param_type_id)
        enum = self.require(EnumType, value.enum_type_id)
        codes = {"number": "real", "string": "str", "integer": "int", "int": "int", "real": "real", "str": "str", "enum": "enum"}
        if enum.code != "param_type" or value.code not in codes:
            raise BusinessRuleError("Конфигуратор поддерживает целые, вещественные, строки и перечисления")
        return codes[value.code]

    def config_params(self, item_id):
        """GET_CONFIG_PARAMS: наследование назначений класса, ближайшее переопределяет."""
        item = self.template(item_id)
        class_id, seen, assigned = item.item_class_id, set(), {}
        while class_id is not None:
            if class_id in seen:
                raise BusinessRuleError("Цикл классификатора изделий")
            seen.add(class_id)
            for row in self.repo.rows(ClassConfigurationParameter, class_id=class_id):
                assigned.setdefault(row.parameter_id, row)
            class_id = self.require(ItemClassifier, class_id).parent_id
        result = []
        for row in sorted(assigned.values(), key=lambda r: (r.display_order, r.parameter_id)):
            if row.flag_conf:
                parameter = self.require(Parameter, row.parameter_id)
                result.append({**row.model_dump(), "code": parameter.code, "name": parameter.name,
                               "type": self.parameter_type(parameter), "enum_type_id": parameter.enum_type_id,
                               "unit_simple_id": parameter.unit_simple_id})
        return result

    def validated_values(self, item_id, values):
        specs = self.config_params(item_id)
        by_code = {row["code"]: row for row in specs}
        if set(values) - set(by_code):
            raise BusinessRuleError("Переданы неизвестные параметры конфигурации")
        result = {}
        for code, spec in by_code.items():
            if code not in values:
                if spec["required"]:
                    raise BusinessRuleError(f"Обязателен параметр {code}")
                continue
            value, typ = values[code], spec["type"]
            if typ in ("int", "real"):
                value = ConstraintInterpreter.typed(value, "number")
                if typ == "int" and value != value.to_integral_value():
                    raise BusinessRuleError(f"Параметр {code} должен быть целым")
                if abs(value) >= Decimal("1e12") or value.as_tuple().exponent < -6:
                    raise BusinessRuleError(f"Точность параметра {code} превышает 18,6")
                if (spec["min_value"] is not None and value < spec["min_value"]) or (
                    spec["max_value"] is not None and value > spec["max_value"]
                ):
                    raise BusinessRuleError(f"Параметр {code} вне диапазона")
            elif typ == "str":
                value = ConstraintInterpreter.typed(value, "string")
                if len(value) > 500:
                    raise BusinessRuleError(f"Параметр {code} слишком длинный")
            else:
                if type(value) is not int:
                    raise BusinessRuleError(f"Параметр {code}: ожидается ID значения перечисления")
                enum_value = self.require(EnumValue, value)
                if enum_value.enum_type_id != spec["enum_type_id"]:
                    raise BusinessRuleError(f"Параметр {code}: другое перечисление")
                value = Decimal(value)
            result[code] = value
        return specs, result

    def interpreter(self):
        return ConstraintInterpreter({row.code: row.definition for row in self.repo.rows(ConfigurationFunction)})

    def check_constraints(self, item_id, values):
        """CHECK_CONSTRAINTS: проверяет все правила типового изделия."""
        _, context = self.validated_values(item_id, values)
        failed = []
        for rule in self.repo.rows(ConfigurationConstraint, template_id=item_id):
            try:
                result = self.interpreter().evaluate(rule.expression, context)
                if ConstraintInterpreter.typed(result, "bool") is not True:
                    failed.append(rule.name)
            except BusinessRuleError as exc:
                raise BusinessRuleError(f"Ограничение «{rule.name}»: {exc.detail}") from exc
        return {"valid": not failed, "violations": failed}

    def create_variant(self, item_id, data):
        """CREATE_VARIANT: Item + его значения, атомарно в транзакции запроса."""
        self.repo.lock()
        base = self.template(item_id)
        check = self.check_constraints(item_id, data.values)
        if not check["valid"]:
            raise BusinessRuleError("Нарушены ограничения: " + "; ".join(check["violations"]))
        specs, _ = self.validated_values(item_id, data.values)
        if self.repo.rows(Item, number=data.number):
            raise ConflictError("Обозначение изделия занято")
        variant = self.repo.save(Item(number=data.number, name=data.name, item_class_id=base.item_class_id,
                                      item_type_id=base.item_type_id, article=base.article))
        self.repo.save(ItemConfiguration(item_id=variant.id, kind="variant", template_id=item_id))
        for unit in self.repo.rows(UnitQuantity, item_id=base.id):
            self.repo.save(UnitQuantity(item_id=variant.id, unit_simple_id=unit.unit_simple_id,
                                       coefficient=unit.coefficient, is_base=unit.is_base))
        for spec in specs:
            if spec["code"] in data.values:
                self.repo.save(VariantParameterValue(item_id=variant.id, parameter_id=spec["parameter_id"],
                                                     value=data.values[spec["code"]]))
        return self.variant_document(variant.id)

    def variant_document(self, item_id):
        item = self.require(Item, item_id)
        meta = self.repo.get(ItemConfiguration, item_id)
        values = {self.require(Parameter, row.parameter_id).code: row.value
                  for row in self.repo.rows(VariantParameterValue, item_id=item_id)}
        details = []
        for row in self.repo.rows(VariantParameterValue, item_id=item_id):
            parameter = self.require(Parameter, row.parameter_id)
            value = row.value
            if self.parameter_type(parameter) == "enum":
                value = self.require(EnumValue, value).name
            unit = self.repo.get(UnitSimple, parameter.unit_simple_id) if parameter.unit_simple_id else None
            details.append({"code": parameter.code, "name": parameter.name, "value": value,
                            "unit": unit.cond_symbol_1 if unit else None})
        base = next((u for u in self.repo.rows(UnitQuantity, item_id=item_id) if u.is_base), None)
        base_unit = self.require(UnitSimple, base.unit_simple_id).cond_symbol_1 if base else None
        return {"item": item, "configuration": meta, "values": values, "parameter_details": details,
                "base_unit": base_unit}

    def save_function(self, data):
        self.repo.lock()
        if self.repo.rows(ConfigurationFunction, code=data.code):
            raise ConflictError("Код функции занят")
        definition = data.definition.model_dump()
        functions = {row.code: row.definition for row in self.repo.rows(ConfigurationFunction)}
        functions[data.code] = definition
        expression = {"kind": "call", "function": data.code, "args": {
            name: {"kind": "param", "name": name} for name in definition["parameters"]}}
        ConstraintInterpreter(functions).validate(expression, definition["parameters"])
        return self.repo.save(ConfigurationFunction(code=data.code, name=data.name,
                                                     definition=data.definition.model_dump()))

    def save_constraint(self, item_id, data):
        self.repo.lock()
        self.template(item_id)
        if self.repo.rows(ItemConfiguration, template_id=item_id):
            raise ConflictError("У шаблона уже есть варианты; менять правила нельзя")
        parameters = {row["code"]: "string" if row["type"] == "str" else "number"
                      for row in self.config_params(item_id)}
        if self.interpreter().validate(data.expression, parameters) != "bool":
            raise BusinessRuleError("Ограничение должно возвращать логический результат")
        return self.repo.save(ConfigurationConstraint(template_id=item_id, **data.model_dump()))

    def ensure_class_mutable(self, class_id):
        # Менять опубликованную конфигурационную модель при существующих вариантах нельзя.
        for meta in self.repo.rows(ItemConfiguration, kind="variant"):
            item = self.require(Item, meta.template_id)
            cursor, seen = item.item_class_id, set()
            while cursor is not None and cursor not in seen:
                if cursor == class_id:
                    raise ConflictError("Класс используется сохранёнными вариантами")
                seen.add(cursor)
                cursor = self.require(ItemClassifier, cursor).parent_id

    def change_parameter(self, class_id, parameter_id, data=None):
        self.repo.lock()
        rows = self.repo.rows(ClassConfigurationParameter, class_id=class_id, parameter_id=parameter_id)
        if not rows:
            raise NotFoundError("Назначение параметра не найдено")
        self.ensure_class_mutable(class_id)
        row = rows[0]
        if data is None:
            self.repo.delete(row)
            return None
        if data.parameter_id != parameter_id:
            raise BusinessRuleError("Идентификатор параметра нельзя менять")
        for key, value in data.model_dump().items():
            setattr(row, key, value)
        return self.repo.save(row)

    def delete_constraint(self, item_id, constraint_id):
        self.repo.lock()
        self.template(item_id)
        row = self.require(ConfigurationConstraint, constraint_id)
        if row.template_id != item_id:
            raise NotFoundError("Ограничение не принадлежит шаблону")
        if self.repo.rows(ItemConfiguration, template_id=item_id):
            raise ConflictError("У шаблона уже есть варианты; менять правила нельзя")
        self.repo.delete(row)

    def update_order(self, order_id, data):
        row = self.draft(order_id)
        if data.ho_id is not None:
            self.require(Ho, data.ho_id)
        for key, value in data.model_dump().items():
            setattr(row, key, value)
        return self.repo.save(row)

    def delete_order(self, order_id):
        row = self.draft(order_id)
        for position in self.repo.rows(CustomerOrderPosition, order_id=order_id):
            self.repo.delete(position)
        self.repo.delete(row)

    def order_cost(self, order_id, pricelist_set_id):
        """Калькуляция заказа через маршруты конкретных изделий (№6)."""
        from src.repository.technology_repository import TechnologyRepository
        from src.services.technology_service import TechnologyService
        document = self.order_document(order_id)
        if not document["positions"]:
            raise BusinessRuleError("Заказ пуст")
        technology = TechnologyService(TechnologyRepository(self.repo.session))
        lines = []
        for position in document["positions"]:
            try:
                cost = technology.cost(position["item_id"], position["quantity"], pricelist_set_id)
            except (BusinessRuleError, NotFoundError) as exc:
                raise ConflictError(f"Для позиции {position['number']} требуется маршрут конкретного изделия: {exc.detail}") from exc
            lines.append({"number": position["number"], **cost})
        return {"order_id": order_id, "currency": "RUB", "positions": lines,
                "total_cost": sum((line["total_cost"] for line in lines), Decimal("0.00"))}

    def create_order(self, data):
        if data.ho_id is not None:
            self.require(Ho, data.ho_id)
        return self.repo.save(CustomerOrder(**data.model_dump()))

    def draft(self, order_id):
        self.repo.lock()
        order = self.require(CustomerOrder, order_id)
        if order.status != "draft":
            raise ConflictError("Согласованный заказ нельзя изменять")
        return order

    def put_position(self, order_id, data, position_id=None):
        """ADD_TO_ORDER: простое изделие или конкретный вариант, количество в базовой ЕИ."""
        self.draft(order_id)
        self.require(Item, data.item_id)
        meta = self.repo.get(ItemConfiguration, data.item_id)
        if meta and meta.kind == "template":
            raise BusinessRuleError("В заказ нужно добавить вариант, а не шаблон")
        if not any(u.is_base for u in self.repo.rows(UnitQuantity, item_id=data.item_id)):
            raise BusinessRuleError("Изделию необходима базовая единица количества")
        if position_id is None:
            row = CustomerOrderPosition(order_id=order_id, **data.model_dump())
        else:
            row = self.require(CustomerOrderPosition, position_id)
            if row.order_id != order_id:
                raise NotFoundError("Позиция не принадлежит заказу")
            for key, value in data.model_dump().items():
                setattr(row, key, value)
        return self.repo.save(row)

    def delete_position(self, order_id, position_id):
        self.draft(order_id)
        row = self.require(CustomerOrderPosition, position_id)
        if row.order_id != order_id:
            raise NotFoundError("Позиция не принадлежит заказу")
        self.repo.delete(row)

    def order_document(self, order_id):
        order = self.require(CustomerOrder, order_id)
        rows = sorted(self.repo.rows(CustomerOrderPosition, order_id=order_id), key=lambda r: r.number)
        return {"order": order, "positions": [
            {**row.model_dump(), **self.variant_document(row.item_id)} for row in rows]}

    def agree_order(self, order_id):
        order = self.draft(order_id)
        if not self.repo.rows(CustomerOrderPosition, order_id=order_id):
            raise BusinessRuleError("Пустой заказ нельзя согласовать")
        order.status = "agreed"
        return self.repo.save(order)
