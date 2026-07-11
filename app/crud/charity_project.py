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

    async def get_projects_by_completion_rate(
            self, session: AsyncSession,
    ) -> list[CharityProject]:
        """Закрытые проекты, отсортированные по скорости сбора средств."""
        projects = (
            await session.execute(
                select(CharityProject).where(CharityProject.fully_invested)
            )
        ).scalars().all()
        return sorted(
            projects,
            key=lambda project: project.close_date - project.create_date,
        )


charity_project_crud = CRUDCharityProject(CharityProject)
