import logging
from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, Query, status
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import SessionManager
from app.core.security import oauth2_scheme
from app.models.clients import Client
from app.models.items import Item
from app.schemas.token import TokenData
from app.services import items as service_items
from app.services.clients import service_client

EXPIRED_JWT = "Expired JWT"
INVALID_JWT = "Invalid JWT"

logger = logging.getLogger(__name__)


@dataclass
class PaginationParams:
    page: int
    per_page: int


def paginate(default_per_page: int = 50):
    def _pagination(
        page: int = Query(
            1,
            ge=1,
            description="Page number, starting from 1",
        ),
        per_page: int = Query(
            default_per_page,
            ge=1,
            le=50,
            description="Number of results per page",
        ),
    ) -> PaginationParams:
        return PaginationParams(page=page, per_page=per_page)

    return _pagination


async def get_db_session():
    async with SessionManager() as db_session:
        yield db_session


def check_client(client: Client | None) -> Client:
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


def get_token_data(token: str = Depends(oauth2_scheme)) -> TokenData:
    try:
        payload = jwt.decode(
            jwt=token,
            key=settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        token_data = TokenData(client_id=payload.get("sub"))
    except ExpiredSignatureError:
        service_client.raise_unauthorized(EXPIRED_JWT)
    except (PyJWTError, ValidationError) as e:
        logger.warning(f"Invalid JWT: {e}")
        service_client.raise_unauthorized(INVALID_JWT)

    return token_data


async def get_current_client(
    token: TokenData = Depends(get_token_data),
    db_session: AsyncSession = Depends(get_db_session),
) -> Client:
    if token.client_id is None:
        logger.warning("Token does not contain client_id")
        service_client.raise_unauthorized(INVALID_JWT)

    client = check_client(
        await service_client.get(db_session, oauth_id=token.client_id)
    )

    return client


async def get_current_admin_client(
    current_client: Client = Depends(get_current_client),
) -> Client:
    if not current_client.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    return current_client


async def get_client_by_id(
    id: int,
    db_session: AsyncSession = Depends(get_db_session),
) -> Client:
    client = check_client(await service_client.get(db_session, id=id))
    return client


async def get_item_by_id(
    id: int,
    client: Client = Depends(get_current_client),
    db_session: AsyncSession = Depends(get_db_session),
) -> Item:
    item = await service_items.get(db_session, id, owner_id=client.id)

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    return item
