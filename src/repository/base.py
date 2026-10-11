from typing import Any, Generic, Optional, Sequence, Type, TypeVar

from sqlmodel import SQLModel, Session, select

ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseRepository(Generic[ModelType]):
    """Базовый репозиторий с CRUD-методами.

    Репозиторий не фиксирует транзакцию: изменения отправляются в БД через
    flush(), а commit/rollback выполняет get_session() один раз на запрос.
    Поэтому составные операции сервиса (несколько вставок) атомарны.
    """

    def __init__(self, model: Type[ModelType], session: Session) -> None:
        self.model = model
        self.session = session

    def get_by_id(self, obj_id: int) -> Optional[ModelType]:
        return self.session.get(self.model, obj_id)

    def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        result = self.session.exec(select(self.model).offset(skip).limit(limit))
        return result.all()

    def create(self, data: dict[str, Any]) -> ModelType:
        obj = self.model(**data)
        self.session.add(obj)
        self.session.flush()
        self.session.refresh(obj)
        return obj

    def update(self, obj: ModelType, data: dict[str, Any]) -> ModelType:
        for key, value in data.items():
            setattr(obj, key, value)
        self.session.add(obj)
        self.session.flush()
        self.session.refresh(obj)
        return obj

    def delete(self, obj: ModelType) -> None:
        self.session.delete(obj)
        self.session.flush()
