from app.schemas.base import BaseModel, NonEmptyModel


class ItemSchema(BaseModel):
    id: int
    title: str
    description: str


class ItemCreate(BaseModel):
    title: str
    description: str


class ItemUpdate(NonEmptyModel):
    title: str | None = None
    description: str | None = None
