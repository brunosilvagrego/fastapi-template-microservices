from pydantic import BaseModel, ConfigDict


# Shared properties
class ItemBase(BaseModel):
    title: str
    description: str | None = None


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = None


# Properties to return to client
class ItemPublic(ItemBase):
    id: int
    owner_id: int

    model_config = ConfigDict(from_attributes=True)
