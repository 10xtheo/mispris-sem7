"""Доменные исключения сервисного слоя.

Сервисы не знают про HTTP: они выбрасывают эти исключения,
а обработчик в src/main.py переводит их в HTTP-ответы.
"""


class DomainError(Exception):
    """Базовое доменное исключение."""

    status_code: int = 400

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class NotFoundError(DomainError):
    """Объект не найден (HTTP 404)."""

    status_code = 404


class BusinessRuleError(DomainError):
    """Нарушено бизнес-правило или ограничение предметной области (HTTP 400)."""

    status_code = 400


class ConflictError(DomainError):
    """Конфликт с текущим состоянием данных: дубликат, занятая связь (HTTP 409)."""

    status_code = 409
