from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class CRUDBase:
    """Базовый класс CRUD-операций."""

    def __init__(self, model):
        self.model = model

    async def get(self, obj_id: int, session: AsyncSession):
        return (
            await session.execute(
                select(self.model).where(self.model.id == obj_id)
            )
        ).scalars().first()

    async def get_multi(self, session: AsyncSession):
        return (await session.execute(select(self.model))).scalars().all()

    async def get_open_objects(self, session: AsyncSession):
        """Открытые объекты в порядке их создания."""
        return (
            await session.execute(
                select(self.model).where(
                    self.model.fully_invested.is_(False)
                ).order_by(self.model.create_date, self.model.id)
            )
        ).scalars().all()

    async def create(
            self,
            obj_in,
            session: AsyncSession,
            commit: bool = True,
            user: Optional[User] = None,
    ):
        data = obj_in.model_dump()
        if user is not None:
            data['user_id'] = user.id
        db_obj = self.model(**data)
        session.add(db_obj)
        if commit:
            await session.commit()
            await session.refresh(db_obj)
        return db_obj

    async def update(
            self, db_obj, obj_in, session: AsyncSession, commit: bool = True,
    ):
        for field, value in obj_in.model_dump(exclude_unset=True).items():
            setattr(db_obj, field, value)
        if commit:
            await session.commit()
            await session.refresh(db_obj)
        return db_obj

    async def remove(self, db_obj, session: AsyncSession):
        await session.delete(db_obj)
        await session.commit()
        return db_obj
