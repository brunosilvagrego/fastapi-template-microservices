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
    """Service layer for ``Client`` management.

    Extends :class:`~app.services.crud.CRUDBase` with business logic for
    OAuth2 client-credential authentication, credential generation, soft
    deletion, and admin-level CRUD operations.
    """

    def raise_unauthorized(
        self,
        detail: str = "Incorrect client_id or client_secret",
    ) -> Never:
        """Raise an HTTP 401 Unauthorized exception.

        Centralises the construction of 401 responses so that authentication
        failures always surface the same error shape to callers.

        Args:
            detail: Human-readable error message included in the response body.
                Defaults to a generic credential-mismatch message.

        Raises:
            HTTPException: Always raised with status ``401 Unauthorized``.
        """
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
        """Validate OAuth2 client credentials and return an access token.

        Looks up the client by ``client_id``, verifies the provided
        ``client_secret`` against the stored hash, and issues a signed JWT on
        success.

        Args:
            db_session: The active async database session.
            client_id: The OAuth2 ``client_id`` submitted by the caller.
            client_secret: The plaintext ``client_secret`` submitted by the
                caller.

        Returns:
            A :class:`~app.schemas.token.Token` containing the signed JWT
            access token and its type.

        Raises:
            HTTPException: ``401 Unauthorized`` when either credential is
                ``None``, the client does not exist, or the secret does not
                match the stored hash.
        """
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
        """Register a new OAuth2 client and return its credentials.

        Generates a unique ``client_id`` / ``client_secret`` pair, stores the
        hashed secret, and returns the plaintext secret **once** in the
        response. The plaintext secret is never persisted and cannot be
        retrieved again.

        Args:
            db_session: The active async database session.
            create_schema: Public-facing creation payload containing the
                client ``name`` and optional ``is_admin`` flag.

        Returns:
            A :class:`~app.schemas.clients.ClientCreateResponse` that includes
            the generated ``client_id`` and plaintext ``client_secret``.

        Raises:
            HTTPException: ``409 Conflict`` when a client with the same
                ``oauth_id`` already exists (rare collision). ``500 Internal
                Server Error`` for any other persistence failure.
        """
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
        """Return a paginated list of clients.

        Args:
            db_session: The active async database session.
            page: 1-based page number.
            per_page: Maximum number of clients to return per page.
            active_only: When ``True``, only clients whose ``deleted_at`` is
                ``NULL`` (i.e. not soft-deleted) are included.

        Returns:
            A sequence of :class:`~app.models.clients.Client` ORM instances
            for the requested page.
        """
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
        """Apply an admin update to a client, optionally rotating credentials.

        When ``update_schema.regenerate_credentials`` is ``True``, a fresh
        ``client_id`` / ``client_secret`` pair is generated and the new
        plaintext secret is returned in the response (it is not stored).

        Args:
            db_session: The active async database session.
            client: The :class:`~app.models.clients.Client` ORM instance to
                update.
            update_schema: Admin update payload; may include a new ``name``,
                ``is_admin`` flag, and/or a credential-rotation request.

        Returns:
            A :class:`~app.schemas.clients.ClientUpdateResponse` reflecting
            the updated state. ``client_id`` and ``client_secret`` are
            ``None`` when credentials were not regenerated.

        Raises:
            HTTPException: ``500 Internal Server Error`` if the underlying
                update operation returns ``None``.
        """
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
        """Soft-delete a client by setting its ``deleted_at`` timestamp.

        The client record is retained in the database but is excluded from
        active-only queries. This operation is irreversible through the
        standard API surface.

        Args:
            db_session: The active async database session.
            client: The :class:`~app.models.clients.Client` ORM instance to
                deactivate.
        """
        client.deleted_at = now_utc()
        await db_session.commit()
        await db_session.refresh(client)


service_client = ServiceClient(Client)
