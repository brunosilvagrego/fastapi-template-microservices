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


@router.post("/token")
async def new_access_token(
    form: Annotated[OAuth2ClientCredentialsRequestForm, Depends()],
    db_session: AsyncSession = Depends(get_db_session),
) -> Token:
    return await service_client.authenticate(
        db_session,
        client_id=form.client_id,
        client_secret=form.client_secret,
    )
