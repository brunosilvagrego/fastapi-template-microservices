import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session
from app.core.security import OAuth2ClientCredentialsRequestForm
from app.schemas.token import Token
from app.services.clients import service_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/token",
    summary="Obtain an access token",
    description=(
        "Exchange a valid **client_id** and **client_secret** pair for a "
        "short-lived JWT bearer token. The token must be included in the "
        "`Authorization: Bearer <token>` header of all subsequent requests "
        "to protected endpoints.\n\n"
        "Credentials are submitted as an `application/x-www-form-urlencoded` "
        "body following the OAuth 2.0 Client Credentials grant (RFC 6749 §4.4)."
    ),
    response_description="A bearer access token.",
    responses={
        401: {
            "description": "Invalid credentials — the client_id does not exist "
            "or the client_secret does not match.",
        },
    },
)
async def new_access_token(
    form: Annotated[OAuth2ClientCredentialsRequestForm, Depends()],
    db_session: AsyncSession = Depends(get_db_session),
) -> Token:
    """Issue a JWT access token using the OAuth2 Client Credentials flow.

    Validates the supplied ``client_id`` and ``client_secret`` against the
    database. On success, a signed JWT is returned. The token encodes the
    ``client_id`` in the ``sub`` claim and expires according to the
    application's JWT settings.

    Args:
        form: Parsed ``application/x-www-form-urlencoded`` form containing
            ``client_id`` and ``client_secret``.
        db_session: Injected async database session.

    Returns:
        A :class:`~app.schemas.token.Token` with ``access_token`` and
        ``token_type`` fields.

    Raises:
        HTTPException: ``401 Unauthorized`` when either credential is missing
            or incorrect.
    """
    return await service_client.authenticate(
        db_session,
        client_id=form.client_id,
        client_secret=form.client_secret,
    )
