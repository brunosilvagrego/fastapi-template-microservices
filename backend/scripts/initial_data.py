import asyncio
import logging

from app.core.config import settings
from app.core.database import SessionLocal
from app.crud.users import create_user, get_user_by_email
from app.schemas.users import UserCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init() -> None:
    async with SessionLocal() as session:
        user = await get_user_by_email(session=session, email=settings.FIRST_SUPERUSER)
        if not user:
            user_in = UserCreate(
                email=settings.FIRST_SUPERUSER,
                password=settings.FIRST_SUPERUSER_PASSWORD,
                is_superuser=True,
                is_active=True,
                full_name="Initial Super User",
            )
            await create_user(session=session, user_create=user_in)
            logger.info(f"Superuser {settings.FIRST_SUPERUSER} created")
        else:
            logger.info(f"Superuser {settings.FIRST_SUPERUSER} already exists")


async def main() -> None:
    logger.info("Creating initial data")
    await init()
    logger.info("Initial data created")


if __name__ == "__main__":
    asyncio.run(main())
