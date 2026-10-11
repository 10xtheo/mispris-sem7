from sqlmodel import SQLModel


class Message(SQLModel):
    detail: str


class PaginationParams(SQLModel):
    skip: int = 0
    limit: int = 100
