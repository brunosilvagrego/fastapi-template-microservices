from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_password_hash, verify_password
from app.models.users import User
from app.schemas.users import UserCreate, UserUpdate


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = await session.execute(statement)
    return session_user.scalars().first()


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    session_user = await session.get(User, user_id)
    return session_user


async def create_user(session: AsyncSession, user_create: UserCreate) -> User:
    db_obj = User(
        email=user_create.email,
        hashed_password=get_password_hash(user_create.password),
        full_name=user_create.full_name,
        is_superuser=user_create.is_superuser,
        is_active=user_create.is_active,
    )
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def authenticate(
    session: AsyncSession, email: str, password: str
) -> User | None:
    user = await get_user_by_email(session=session, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def update_user(
    session: AsyncSession, db_user: User, user_in: UserUpdate
) -> User:
    user_data = user_in.model_dump(exclude_unset=True)
    if "password" in user_data and user_data["password"]:
        hashed_password = get_password_hash(user_data["password"])
        del user_data["password"]
        user_data["hashed_password"] = hashed_password

    for key, value in user_data.items():
        setattr(db_user, key, value)

    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user
