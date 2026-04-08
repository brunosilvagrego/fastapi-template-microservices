import logging
from collections.abc import Sequence
from typing import Never

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.consts import ENTITY_CREATION_ERROR
from app.core.security import (
    create_access_token,
    new_client_credentials,
    verify_password,
)
from app.core.utils import now_utc
from app.models.clients import Client
from app.schemas.clients import (
    ClientCreate,
    ClientCreatePrivate,
    ClientCreateResponse,
    ClientUpdate,
    ClientUpdatePrivate,
    ClientUpdateResponse,
)
from app.schemas.token import Token
from app.services.crud import CRUDBase

logger = logging.getLogger(__name__)


class ServiceClient(CRUDBase[Client, ClientCreatePrivate, ClientUpdatePrivate]):
    def raise_unauthorized(
        self,
        detail: str = "Incorrect client_id or client_secret",
    ) -> Never:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )

    async def authenticate(
        self,
        db_session: AsyncSession,
        client_id: str | None,
        client_secret: str | None,
    ) -> Token:
        if client_id is None or client_secret is None:
            self.raise_unauthorized()

        client = await self.get(db_session, oauth_id=client_id)

        if client is None:
            self.raise_unauthorized()

        if not verify_password(client_secret, client.oauth_secret_hash):
            self.raise_unauthorized()

        access_token = create_access_token(data={"sub": client.oauth_id})

        return Token(
            access_token=access_token,
            token_type=settings.JWT_TOKEN_TYPE,
        )

    async def new(
        self,
        db_session: AsyncSession,
        create_schema: ClientCreate,
    ) -> ClientCreateResponse:
        client_id, client_secret, client_secret_hash = new_client_credentials()

        try:
            client = await self.create(
                db_session,
                create_schema=ClientCreatePrivate(
                    name=create_schema.name,
                    is_admin=create_schema.is_admin,
                    oauth_id=client_id,
                    oauth_secret_hash=client_secret_hash,
                ),
            )
        except Exception as err:  # noqa: BLE001
            logger.error(
                ENTITY_CREATION_ERROR,
                Client.__name__,
                create_schema.model_dump_json(),
                err,
            )

            if isinstance(err, IntegrityError):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A Client with the same oauth_id already exists.",
                ) from None

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register client.",
            ) from None

        return ClientCreateResponse(
            id=client.id,
            name=client.name,
            created_at=client.created_at,
            deleted_at=client.deleted_at,
            is_admin=client.is_admin,
            client_id=client.oauth_id,
            client_secret=client_secret,
        )

    async def get_many(
        self,
        db_session: AsyncSession,
        page: int,
        per_page: int,
        active_only: bool,
    ) -> Sequence[Client]:
        filters = [Client.deleted_at.is_(None)] if active_only else []

        return await self.get_multi(
            db_session,
            *filters,
            page=page,
            per_page=per_page,
        )

    async def admin_update(
        self,
        db_session: AsyncSession,
        client: Client,
        update_schema: ClientUpdate,
    ) -> ClientUpdateResponse:
        new_client_id, new_client_secret, new_client_secret_hash = (
            new_client_credentials()
            if update_schema.regenerate_credentials
            else (None, None, None)
        )

        updated_client = await self.update(
            db_session,
            db_object=client,
            update_schema=ClientUpdatePrivate(
                name=update_schema.name,
                is_admin=update_schema.is_admin,
                oauth_id=new_client_id,
                oauth_secret_hash=new_client_secret_hash,
            ),
        )

        if updated_client is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update client.",
            )

        return ClientUpdateResponse(
            id=updated_client.id,
            name=updated_client.name,
            created_at=updated_client.created_at,
            deleted_at=updated_client.deleted_at,
            is_admin=updated_client.is_admin,
            client_id=new_client_id,
            client_secret=new_client_secret,
        )

    async def deactivate(
        self,
        db_session: AsyncSession,
        client: Client,
    ) -> None:
        client.deleted_at = now_utc()
        await db_session.commit()
        await db_session.refresh(client)


service_client = ServiceClient(Client)
