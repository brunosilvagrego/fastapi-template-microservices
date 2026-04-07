from pydantic import ConfigDict

from app.schemas.base import BaseModel, NonEmptyModel


class ItemBase(BaseModel):
    title: str
    description: str


class ItemCreate(ItemBase):
    model_config = ConfigDict(extra="forbid")


class ItemCreatePrivate(ItemBase):
    owner_id: int

    model_config = ConfigDict(extra="forbid")


class ItemRead(ItemBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class ItemUpdate(NonEmptyModel):
    title: str | None = None
    description: str | None = None

    model_config = ConfigDict(extra="forbid")
