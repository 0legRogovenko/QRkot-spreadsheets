from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.validators import (check_charity_project_exists,
                                check_charity_project_has_no_investments,
                                check_charity_project_not_closed,
                                check_full_amount_not_less_invested,
                                check_name_duplicate)
from app.core.db import get_async_session
from app.core.user import current_superuser
from app.crud.charity_project import charity_project_crud
from app.crud.donation import donation_crud
from app.schemas.charity_project import (CharityProjectCreate,
                                         CharityProjectDB,
                                         CharityProjectUpdate)
from app.services.investment import invest

router = APIRouter()


@router.get(
    '/',
    response_model=list[CharityProjectDB],
    response_model_exclude_none=True,
)
async def get_all_charity_projects(
        session: AsyncSession = Depends(get_async_session),
):
    """Показать список всех целевых проектов."""
    return await charity_project_crud.get_multi(session)


@router.post(
    '/',
    response_model=CharityProjectDB,
    response_model_exclude_none=True,
    dependencies=[Depends(current_superuser)],
)
async def create_charity_project(
        project: CharityProjectCreate,
        session: AsyncSession = Depends(get_async_session),
):
    """Создать целевой проект.

    Только для суперюзеров.
    """
    await check_name_duplicate(project.name, session)
    new_project = await charity_project_crud.create(
        project, session, commit=False
    )
    session.add_all(
        invest(new_project, await donation_crud.get_open_objects(session))
    )
    await session.commit()
    await session.refresh(new_project)
    return new_project


@router.patch(
    '/{project_id}',
    response_model=CharityProjectDB,
    response_model_exclude_none=True,
    dependencies=[Depends(current_superuser)],
)
async def update_charity_project(
        project_id: int,
        obj_in: CharityProjectUpdate,
        session: AsyncSession = Depends(get_async_session),
):
    """Редактировать целевой проект.

    Только для суперюзеров.
    Закрытый проект нельзя редактировать;
    нельзя установить требуемую сумму меньше уже вложенной.
    """
    project = await check_charity_project_exists(project_id, session)
    check_charity_project_not_closed(project)
    if obj_in.name is not None and obj_in.name != project.name:
        await check_name_duplicate(obj_in.name, session)
    if obj_in.full_amount is not None:
        check_full_amount_not_less_invested(project, obj_in.full_amount)
    project = await charity_project_crud.update(
        project, obj_in, session, commit=False
    )
    project.close_if_fully_invested()
    await session.commit()
    await session.refresh(project)
    return project


@router.delete(
    '/{project_id}',
    response_model=CharityProjectDB,
    response_model_exclude_none=True,
    dependencies=[Depends(current_superuser)],
)
async def delete_charity_project(
        project_id: int,
        session: AsyncSession = Depends(get_async_session),
):
    """Удалить целевой проект.

    Только для суперюзеров.
    Нельзя удалить проект, в который уже были инвестированы средства.
    """
    project = await check_charity_project_exists(project_id, session)
    check_charity_project_has_no_investments(project)
    return await charity_project_crud.remove(project, session)
