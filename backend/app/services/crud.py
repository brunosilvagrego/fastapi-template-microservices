from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase


class CRUDBase[
    ModelType: DeclarativeBase,
    CreateSchemaType: BaseModel,
    UpdateSchemaType: BaseModel,
]:
    def __init__(self, model: type[ModelType]):
        self._model = model

    async def create(
        self,
        db_session: AsyncSession,
        create_schema: CreateSchemaType | dict[str, Any],
    ) -> ModelType:
        data = (
            create_schema
            if isinstance(create_schema, dict)
            else create_schema.model_dump(exclude_unset=True)
        )

        db_object = self._model(**data)
        db_session.add(db_object)
        await db_session.commit()
        await db_session.refresh(db_object)

        return db_object

    async def get(
        self,
        db_session: AsyncSession,
        *args,
        **kwargs,
    ) -> ModelType | None:
        stmt = select(self._model)

        if args:
            stmt = stmt.filter(*args)

        if kwargs:
            stmt = stmt.filter_by(**kwargs)

        result = await db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db_session: AsyncSession,
        *args,
        page: int = 1,
        per_page: int = 100,
        **kwargs,
    ) -> Sequence[ModelType]:
        result = await db_session.execute(
            select(self._model)
            .filter(*args)
            .filter_by(**kwargs)
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return result.scalars().all()

    async def update(
        self,
        db_session: AsyncSession,
        *,
        db_object: ModelType | None,
        update_schema: UpdateSchemaType | dict[str, Any],
        exclude_none: bool = True,
        **kwargs,
    ) -> ModelType | None:
        db_object = db_object or await self.get(db_session, **kwargs)

        if db_object is not None:
            data = (
                update_schema
                if isinstance(update_schema, dict)
                else update_schema.model_dump(exclude_unset=True)
            )

            if not data:
                return db_object

            for attribute, value in data.items():
                if exclude_none and value is None:
                    continue
                setattr(db_object, attribute, value)

            await db_session.commit()
            await db_session.refresh(db_object)

        return db_object

    async def delete(
        self,
        db_session: AsyncSession,
        db_object: ModelType | None,
        **kwargs,
    ) -> ModelType | None:
        db_object = db_object or await self.get(db_session, **kwargs)

        if db_object:
            await db_session.delete(db_object)
            await db_session.commit()

        return db_object

    async def bulk_create(
        self,
        db_session: AsyncSession,
        create_schemas: Sequence[CreateSchemaType | dict[str, Any]],
        refresh: bool = False,
    ) -> Sequence[ModelType]:
        db_objects = []

        for create_schema in create_schemas:
            data = (
                create_schema
                if isinstance(create_schema, dict)
                else create_schema.model_dump(exclude_unset=True)
            )
            db_objects.append(self._model(**data))

        db_session.add_all(db_objects)
        await db_session.commit()

        if refresh:
            for db_object in db_objects:
                await db_session.refresh(db_object)

        return db_objects

    async def bulk_update(
        self,
        db_session: AsyncSession,
        updates: Sequence[tuple[ModelType, UpdateSchemaType | dict[str, Any]]],
    ) -> None:
        data_list = []

        for db_object, update_schema in updates:
            data = (
                update_schema
                if isinstance(update_schema, dict)
                else update_schema.model_dump(exclude_unset=True)
            )
            if data:
                data["uid"] = db_object.uid  # type: ignore[attr-defined]
                data_list.append(data)

        await db_session.execute(update(self._model), data_list)
        await db_session.commit()
