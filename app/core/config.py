from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_title: str = 'Благотворительный фонд поддержки котиков QRKot'
    app_description: str = 'Сервис для поддержки котиков'
    database_url: str = 'sqlite+aiosqlite:///./qrkot.db'
    secret: str = 'SECRET'
    jwt_lifetime_seconds: int = 3600
    yandex_disk_token: Optional[str] = None
    report_format: str = '%Y-%m-%d_%H-%M-%S'

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')


settings = Settings()
