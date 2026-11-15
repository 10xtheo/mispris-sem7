from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from html import escape
from sqlmodel import Session

from src.database.database import get_session
from src.models.configuration import ConfigurationConstraint, ConfigurationFunction, CustomerOrder
from src.repository.configuration_repository import ConfigurationRepository
from src.schemas.configuration import (
    ClassParameterInput, ConstraintInput, EvalInput, FunctionInput, OrderInput, PositionInput,
    ValuesInput, VariantInput,
)
from src.services.configuration_service import ConfigurationService
from src.services.constraint_interpreter import ConstraintInterpreter

router = APIRouter()


def service(session: Session = Depends(get_session)):
    return ConfigurationService(ConfigurationRepository(session))


@router.put("/items/{item_id}/configurator", summary="Включить конфигуратор изделия")
def enable_configurator(item_id: int, svc=Depends(service)):
    return svc.enable_template(item_id)


@router.post("/classes/{class_id}/parameters", status_code=201, summary="Назначить параметр конфигурации классу")
def assign_config_parameter(class_id: int, data: ClassParameterInput, svc=Depends(service)):
    return svc.assign_parameter(class_id, data)


@router.get("/items/{item_id}/parameters", summary="Получить параметры конфигурации", description="GET_CONFIG_PARAMS")
def get_config_params(item_id: int, svc=Depends(service)):
    return svc.config_params(item_id)


@router.post("/items/{item_id}/check", summary="Проверить ограничения конфигурации", description="CHECK_CONSTRAINTS")
def check_config_constraints(item_id: int, data: ValuesInput, svc=Depends(service)):
    return svc.check_constraints(item_id, data.values)


@router.post("/items/{item_id}/variants", status_code=201, summary="Создать вариант исполнения", description="CREATE_VARIANT")
def create_config_variant(item_id: int, data: VariantInput, svc=Depends(service)):
    return svc.create_variant(item_id, data)


@router.get("/items/{item_id}/variant", summary="Показать изделие и значения варианта")
def get_config_variant(item_id: int, svc=Depends(service)):
    return svc.variant_document(item_id)


@router.post("/functions", status_code=201, summary="Описать функцию ограничения")
def create_config_function(data: FunctionInput, svc=Depends(service)):
    return svc.save_function(data)


@router.get("/functions", summary="Показать функции ограничений")
def list_config_functions(svc=Depends(service)):
    return svc.repo.rows(ConfigurationFunction)


@router.post("/evaluate", summary="Вычислить выражение ограничения", description="EVAL_FUNCTION")
def evaluate_config_function(data: EvalInput, svc=Depends(service)):
    context = {key: ConstraintInterpreter.typed(value, "number") if type(value) in (int, float) else value
               for key, value in data.values.items()}
    return {"result": svc.interpreter().evaluate(data.expression, context)}


@router.post("/items/{item_id}/constraints", status_code=201, summary="Добавить ограничение шаблона")
def create_config_constraint(item_id: int, data: ConstraintInput, svc=Depends(service)):
    return svc.save_constraint(item_id, data)


@router.get("/items/{item_id}/constraints", summary="Показать ограничения шаблона")
def list_config_constraints(item_id: int, svc=Depends(service)):
    svc.template(item_id)
    return svc.repo.rows(ConfigurationConstraint, template_id=item_id)


@router.post("/orders", status_code=201, summary="Зарегистрировать заказ")
def create_config_order(data: OrderInput, svc=Depends(service)):
    return svc.create_order(data)


@router.get("/orders", summary="Показать заказы")
def list_config_orders(svc=Depends(service)):
    return svc.repo.rows(CustomerOrder)


@router.get("/orders/{order_id}", summary="Сформировать документ состава заказа")
def get_config_order(order_id: int, svc=Depends(service)):
    return svc.order_document(order_id)


@router.post("/orders/{order_id}/positions", status_code=201, summary="Добавить изделие в заказ", description="ADD_TO_ORDER")
def add_config_order_position(order_id: int, data: PositionInput, svc=Depends(service)):
    return svc.put_position(order_id, data)


@router.put("/orders/{order_id}/positions/{position_id}", summary="Изменить позицию заказа")
def update_config_order_position(order_id: int, position_id: int, data: PositionInput, svc=Depends(service)):
    return svc.put_position(order_id, data, position_id)


@router.delete("/orders/{order_id}/positions/{position_id}", status_code=204, summary="Удалить позицию заказа")
def delete_config_order_position(order_id: int, position_id: int, svc=Depends(service)):
    svc.delete_position(order_id, position_id)


@router.post("/orders/{order_id}/agree", summary="Согласовать заказ")
def agree_config_order(order_id: int, svc=Depends(service)):
    return svc.agree_order(order_id)


@router.put("/classes/{class_id}/parameters/{parameter_id}", summary="Изменить назначение параметра")
def update_config_parameter(class_id: int, parameter_id: int, data: ClassParameterInput, svc=Depends(service)):
    return svc.change_parameter(class_id, parameter_id, data)


@router.delete("/classes/{class_id}/parameters/{parameter_id}", status_code=204, summary="Удалить назначение параметра")
def delete_config_parameter(class_id: int, parameter_id: int, svc=Depends(service)):
    svc.change_parameter(class_id, parameter_id)


@router.delete("/items/{item_id}/constraints/{constraint_id}", status_code=204, summary="Удалить ограничение шаблона")
def delete_config_constraint(item_id: int, constraint_id: int, svc=Depends(service)):
    svc.delete_constraint(item_id, constraint_id)


@router.put("/orders/{order_id}", summary="Изменить реквизиты заказа")
def update_config_order(order_id: int, data: OrderInput, svc=Depends(service)):
    return svc.update_order(order_id, data)


@router.delete("/orders/{order_id}", status_code=204, summary="Удалить черновик заказа")
def delete_config_order(order_id: int, svc=Depends(service)):
    svc.delete_order(order_id)


@router.get("/orders/{order_id}/cost", summary="Рассчитать себестоимость заказа")
def cost_config_order(order_id: int, pricelist_set_id: int = Query(gt=0), svc=Depends(service)):
    return svc.order_cost(order_id, pricelist_set_id)


@router.get("/orders/{order_id}/print", response_class=HTMLResponse, summary="Открыть печатную форму заказа")
def print_config_order(order_id: int, svc=Depends(service)):
    document = svc.order_document(order_id)
    order = document["order"]
    lines = []
    for row in document["positions"]:
        item = row["item"]
        values = "; ".join(f"{detail['name']}: {detail['value']} {detail['unit'] or ''}".strip()
                           for detail in row["parameter_details"])
        lines.append("<tr>" + "".join(f"<td>{escape(str(value))}</td>" for value in
            (row["number"], item.number, item.name, values or "—", f"{row['quantity']:g} {row['base_unit'] or ''}")) + "</tr>")
    return """<!doctype html><html lang="ru"><meta charset="utf-8"><title>Состав заказа</title>
<style>body{font:14pt 'Times New Roman',serif;max-width:1000px;margin:30px auto;color:#000}
table{border-collapse:collapse;width:100%}td,th{border:1px solid #444;padding:9px;text-align:left}
@page{size:A4 landscape;margin:20mm}h1{font-size:20pt}button{padding:10px}@media print{button{display:none}}</style>
<button onclick="window.print()">Печать / сохранить PDF</button>""" + (
        f"<h1>Заказ {escape(order.number)}</h1><p>Дата: {order.order_date:%d.%m.%Y}. "
        f"Заказчик: {escape(order.customer)}. Статус: {'согласован' if order.status == 'agreed' else 'черновик'}.</p>"
        "<p>Состав заказа с выбранными параметрами вариантов исполнения.</p>"
        "<table><thead><tr><th>Позиция</th><th>Обозначение</th><th>Изделие</th><th>Параметры варианта</th>"
        "<th>Количество</th></tr></thead><tbody>" + "".join(lines) + "</tbody></table></html>")
