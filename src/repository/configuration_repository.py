from sqlalchemy import text
from sqlmodel import select


class ConfigurationRepository:
    """ORM и блокировки; транзакцией управляет get_session."""
    def __init__(self, session):
        self.session = session

    def get(self, model, key):
        return self.session.get(model, key)

    def rows(self, model, **filters):
        query = select(model)
        for key, value in filters.items():
            query = query.where(getattr(model, key) == value)
        return self.session.exec(query).all()

    def save(self, row):
        self.session.add(row)
        self.session.flush()
        return row

    def delete(self, row):
        self.session.delete(row)
        self.session.flush()

    def lock(self):
        # Единый порядок блокировок для смены конфигуратора и заказа.
        self.session.execute(text("SELECT pg_advisory_xact_lock(7007, 1)"))
