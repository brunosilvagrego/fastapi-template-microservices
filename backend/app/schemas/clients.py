from datetime import datetime

from pydantic import ConfigDict, Field

from app.schemas.base import BaseModel


class ClientBase(BaseModel):
    id: int
    name: str
    created_at: datetime
    deleted_at: datetime | None
    is_admin: bool


class ClientCreate(BaseModel):
    name: str = Field(min_length=1)
    is_admin: bool = False

    model_config = ConfigDict(extra="forbid")


class ClientCreatePrivate(ClientCreate):
    oauth_id: str
    oauth_secret_hash: str

    model_config = ConfigDict(extra="forbid")


class ClientCreateResponse(ClientBase):
    client_id: str
    client_secret: str


class ClientRead(ClientBase):
    model_config = ConfigDict(from_attributes=True)


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    is_admin: bool | None = None
    regenerate_credentials: bool = False

    model_config = ConfigDict(extra="forbid")


class ClientUpdatePrivate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    is_admin: bool | None = None
    oauth_id: str | None = None
    oauth_secret_hash: str | None = None

    model_config = ConfigDict(extra="forbid")


class ClientUpdateResponse(ClientBase):
    client_id: str | None = None
    client_secret: str | None = None
