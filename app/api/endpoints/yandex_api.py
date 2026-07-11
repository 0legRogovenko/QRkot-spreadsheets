from http import HTTPStatus

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.core.user import current_superuser
from app.core.yandex_client import YandexDiskClient, get_yandex_client
from app.crud.charity_project import charity_project_crud
from app.services.yandex_api import create_simple_report

NO_CLOSED_PROJECTS_MESSAGE = 'Закрытые проекты не найдены.'
REPORT_ERROR_TEMPLATE = 'Не удалось сформировать отчёт: {error}'

router = APIRouter()


@router.post(
    '/',
    response_model=str,
    dependencies=[Depends(current_superuser)],
)
async def create_yandex_disk_report(
        session: AsyncSession = Depends(get_async_session),
        client: YandexDiskClient = Depends(get_yandex_client),
):
    """Сформировать на Яндекс Диске отчёт по закрытым проектам.

    Только для суперюзеров.
    Возвращает публичную ссылку на Excel-файл отчёта.
    """
    projects = await charity_project_crud.get_projects_by_completion_rate(
        session
    )
    if not projects:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=NO_CLOSED_PROJECTS_MESSAGE,
        )
    try:
        return await create_simple_report(projects, client)
    except (httpx.HTTPError, ValueError, KeyError) as error:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=REPORT_ERROR_TEMPLATE.format(error=error),
        )
