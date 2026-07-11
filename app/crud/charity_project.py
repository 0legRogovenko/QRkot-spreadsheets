from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.charity_project import CharityProject


class CRUDCharityProject(CRUDBase):

    async def get_project_id_by_name(
            self, project_name: str, session: AsyncSession,
    ) -> Optional[int]:
        return (
            await session.execute(
                select(CharityProject.id).where(
                    CharityProject.name == project_name
                )
            )
        ).scalars().first()

    async def get_closed_projects(
            self, session: AsyncSession,
    ) -> list[CharityProject]:
        """Все закрытые проекты."""
        return (
            await session.execute(
                select(CharityProject).where(CharityProject.fully_invested)
            )
        ).scalars().all()


charity_project_crud = CRUDCharityProject(CharityProject)
