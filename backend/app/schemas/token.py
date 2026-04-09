from pydantic import Field

from app.schemas.base import BaseModel


class Token(BaseModel):
    access_token: str = Field(
        description="JWT access token.",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
    token_type: str = Field(
        description="Type of the token.",
        examples=["Bearer"],
    )


class TokenData(BaseModel):
    client_id: str | None = Field(
        None,
        description="Client ID extracted from the token.",
        examples=["client_123"],
    )
