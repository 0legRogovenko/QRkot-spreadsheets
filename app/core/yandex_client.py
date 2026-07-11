from http import HTTPStatus
from typing import AsyncGenerator, Optional

import httpx
from fastapi import HTTPException

from app.core.config import settings

API_BASE_URL = 'https://cloud-api.yandex.net/v1/disk'
REPORTS_FOLDER = 'QRKot Reports'
REQUEST_TIMEOUT = 30
TOKEN_MISSING_MESSAGE = (
    'Сервис отчётов недоступен: не задан токен Яндекс Диска.'
)
EMPTY_UPLOAD_URL_MESSAGE = (
    'Яндекс Диск вернул пустую ссылку для загрузки файла.'
)


class YandexDiskClient:
    """Асинхронный клиент для работы с API Яндекс Диска."""

    def __init__(self, token: str) -> None:
        self.token = token
        self.session: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> 'YandexDiskClient':
        self.session = httpx.AsyncClient(
            headers={'Authorization': f'OAuth {self.token}'},
            timeout=REQUEST_TIMEOUT,
        )
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.session.aclose()

    async def _create_folder(self) -> None:
        """Создать папку для отчётов, если её ещё нет."""
        response = await self.session.put(
            f'{API_BASE_URL}/resources',
            params={'path': REPORTS_FOLDER},
        )
        if response.status_code == HTTPStatus.CONFLICT:
            return
        response.raise_for_status()

    async def create_excel_file(self, filename: str) -> tuple[str, str]:
        """Получить ссылку для загрузки и путь к файлу на Диске."""
        await self._create_folder()
        disk_path = f'{REPORTS_FOLDER}/{filename}'
        response = await self.session.get(
            f'{API_BASE_URL}/resources/upload',
            params={'path': disk_path, 'overwrite': 'true'},
        )
        response.raise_for_status()
        upload_url = response.json().get('href')
        if not upload_url:
            raise ValueError(EMPTY_UPLOAD_URL_MESSAGE)
        return upload_url, disk_path

    async def upload_file(self, upload_url: str, content: bytes) -> None:
        """Загрузить бинарное содержимое файла по полученной ссылке."""
        response = await self.session.put(upload_url, content=content)
        response.raise_for_status()

    async def publish_file(self, disk_path: str) -> str:
        """Сделать файл публичным и вернуть публичную ссылку."""
        response = await self.session.put(
            f'{API_BASE_URL}/resources/publish',
            params={'path': disk_path},
        )
        response.raise_for_status()
        response = await self.session.get(
            f'{API_BASE_URL}/resources',
            params={'path': disk_path, 'fields': 'public_url'},
        )
        response.raise_for_status()
        return response.json()['public_url']


async def get_yandex_client() -> AsyncGenerator[YandexDiskClient, None]:
    """Зависимость FastAPI: настроенный клиент Яндекс Диска."""
    if not settings.yandex_disk_token:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail=TOKEN_MISSING_MESSAGE,
        )
    async with YandexDiskClient(settings.yandex_disk_token) as client:
        yield client
