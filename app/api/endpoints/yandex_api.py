from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.core.user import current_superuser
from app.core.yandex_client import YandexDiskClient, get_yandex_client
from app.crud.charity_project import charity_project_crud
from app.services.yandex_api import create_simple_report

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
    try:
        return await create_simple_report(
            await charity_project_crud.get_closed_projects(session),
            client,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=REPORT_ERROR_TEMPLATE.format(error=error),
        )
