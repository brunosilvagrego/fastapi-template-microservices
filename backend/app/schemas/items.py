from pydantic import ConfigDict, Field

from app.schemas.base import BaseModel, NonEmptyModel


class ItemBase(BaseModel):
    title: str = Field(
        min_length=1,
        description="Title of the item.",
        examples=["Sample Item"],
    )
    description: str = Field(
        min_length=1,
        description="Description of the item.",
        examples=["This is a sample item description."],
    )


class ItemCreate(ItemBase):
    model_config = ConfigDict(extra="forbid")


class ItemCreatePrivate(ItemBase):
    owner_id: int = Field(
        description="ID of the owner of the item.",
        examples=[123],
    )

    model_config = ConfigDict(extra="forbid")


class ItemRead(ItemBase):
    id: int = Field(description="Unique identifier of the item.", examples=[1])

    model_config = ConfigDict(from_attributes=True)


class ItemUpdate(NonEmptyModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        description="Updated title of the item.",
        examples=["Updated Sample Item"],
    )
    description: str | None = Field(
        default=None,
        min_length=1,
        description="Updated description of the item.",
        examples=["This is an updated sample item description."],
    )

    model_config = ConfigDict(extra="forbid")
