from pydantic import ConfigDict, Field

from app.schemas.base import BaseModel, NonEmptyModel


class ItemBase(BaseModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)


class ItemCreate(ItemBase):
    model_config = ConfigDict(extra="forbid")


class ItemCreatePrivate(ItemBase):
    owner_id: int

    model_config = ConfigDict(extra="forbid")


class ItemRead(ItemBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class ItemUpdate(NonEmptyModel):
    title: str | None = Field(default=None, min_length=1)
    description: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")
