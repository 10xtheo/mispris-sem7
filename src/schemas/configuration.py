from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ClassParameterInput(StrictInput):
    parameter_id: int = Field(gt=0)
    flag_conf: bool = True
    required: bool = True
    display_order: int = Field(default=0, ge=0)
    min_value: Optional[Decimal] = Field(default=None, max_digits=18, decimal_places=6, allow_inf_nan=False)
    max_value: Optional[Decimal] = Field(default=None, max_digits=18, decimal_places=6, allow_inf_nan=False)

    @model_validator(mode="after")
    def range_valid(self):
        if self.min_value is not None and self.max_value is not None and self.min_value > self.max_value:
            raise ValueError("Минимум больше максимума")
        return self


class VariantInput(StrictInput):
    number: str = Field(min_length=1, max_length=50, pattern=r".*\S.*")
    name: str = Field(min_length=1, max_length=500, pattern=r".*\S.*")
    values: dict[str, object]


class FunctionDefinition(StrictInput):
    parameters: dict[str, Literal["number", "string", "bool"]]
    result: Literal["number", "string", "bool"]
    body: dict


class FunctionInput(StrictInput):
    code: str = Field(min_length=1, max_length=50, pattern=r"^[A-Za-z][A-Za-z0-9_]*$")
    name: str = Field(min_length=1, max_length=255)
    definition: FunctionDefinition


class ConstraintInput(StrictInput):
    name: str = Field(min_length=1, max_length=255)
    expression: dict


class ValuesInput(StrictInput):
    values: dict[str, object]


class EvalInput(StrictInput):
    expression: dict
    values: dict[str, object] = Field(default_factory=dict)


class OrderInput(StrictInput):
    number: str = Field(min_length=1, max_length=50, pattern=r".*\S.*")
    customer: str = Field(min_length=1, max_length=255, pattern=r".*\S.*")
    order_date: date
    ho_id: Optional[int] = Field(default=None, gt=0)


class PositionInput(StrictInput):
    number: int = Field(gt=0)
    item_id: int = Field(gt=0)
    quantity: Decimal = Field(gt=0, max_digits=18, decimal_places=6, allow_inf_nan=False)
