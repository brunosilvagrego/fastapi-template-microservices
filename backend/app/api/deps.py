import jwt
from fastapi import Depends, HTTPException, status
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import JWT_ALGORITHM, oauth2_scheme
from app.models.clients import Client
from app.schemas.token import TokenData
from app.services import clients as service_clients

EXPIRED_JWT = "Expired JWT"
INVALID_JWT = "Invalid JWT"


async def get_session():
    async with SessionLocal() as session:
        yield session


def raise_unauthorized(detail: str):
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def get_token_data(token: str = Depends(oauth2_scheme)) -> TokenData:
    try:
        payload = jwt.decode(
            jwt=token,
            key=settings.JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )
        token_data = TokenData(client_id=payload.get("sub"))
    except ExpiredSignatureError:
        raise_unauthorized(EXPIRED_JWT)
    except PyJWTError, ValidationError:
        raise_unauthorized(INVALID_JWT)

    return token_data


async def get_current_client(
    token: TokenData = Depends(get_token_data),
    db_session: AsyncSession = Depends(get_session),
) -> Client:
    if token.client_id is None:
        raise_unauthorized(INVALID_JWT)

    client = await service_clients.get_by_oauth_id(db_session, token.client_id)

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    if not client.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive client",
        )

    return client
