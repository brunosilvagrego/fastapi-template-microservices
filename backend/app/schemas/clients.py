from datetime import datetime

from pydantic import ConfigDict, Field

from app.schemas.base import BaseModel


class ClientBase(BaseModel):
    id: int = Field(
        description="Unique identifier of the client.",
        examples=[1],
    )
    name: str = Field(
        description="Name of the client.",
        examples=["Example Client"],
    )
    created_at: datetime = Field(
        description="Timestamp when the client was created.",
        examples=["2023-01-01T00:00:00Z"],
    )
    deleted_at: datetime | None = Field(
        None,
        description=(
            "Timestamp when the client was soft-deleted, null if not deleted."
        ),
        examples=[None],
    )
    is_admin: bool = Field(
        description="Whether the client has admin privileges.",
        examples=[False],
    )


class ClientCreate(BaseModel):
    name: str = Field(
        min_length=1,
        description="Name of the client to create.",
        examples=["New Client"],
    )
    is_admin: bool = Field(
        False,
        description="Whether the client should have admin privileges.",
        examples=[False],
    )

    model_config = ConfigDict(extra="forbid")


class ClientCreatePrivate(ClientCreate):
    oauth_id: str = Field(
        description="OAuth client ID.",
        examples=["client_123"],
    )
    oauth_secret_hash: str = Field(
        description="Hashed OAuth client secret.",
        examples=["hashed_secret"],
    )

    model_config = ConfigDict(extra="forbid")


class ClientCreateResponse(ClientBase):
    client_id: str = Field(
        description="Generated client ID for authentication.",
        examples=["client_abc123"],
    )
    client_secret: str = Field(
        description="Generated client secret for authentication.",
        examples=["secret_xyz789"],
    )


class ClientRead(ClientBase):
    model_config = ConfigDict(from_attributes=True)


class ClientUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        description="Updated name of the client.",
        examples=["Updated Client Name"],
    )
    is_admin: bool | None = Field(
        None,
        description="Updated admin status of the client.",
        examples=[True],
    )
    regenerate_credentials: bool = Field(
        False,
        description="Whether to regenerate client credentials.",
        examples=[False],
    )

    model_config = ConfigDict(extra="forbid")


class ClientUpdatePrivate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        description="Updated name of the client.",
        examples=["Updated Client Name"],
    )
    is_admin: bool | None = Field(
        None,
        description="Updated admin status of the client.",
        examples=[True],
    )
    oauth_id: str | None = Field(
        None,
        description="Updated OAuth client ID.",
        examples=["new_client_456"],
    )
    oauth_secret_hash: str | None = Field(
        None,
        description="Updated hashed OAuth client secret.",
        examples=["new_hashed_secret"],
    )

    model_config = ConfigDict(extra="forbid")


class ClientUpdateResponse(ClientBase):
    client_id: str | None = Field(
        None,
        description="Updated client ID, if regenerated.",
        examples=["new_client_abc123"],
    )
    client_secret: str | None = Field(
        None,
        description="Updated client secret, if regenerated.",
        examples=["new_secret_xyz789"],
    )
