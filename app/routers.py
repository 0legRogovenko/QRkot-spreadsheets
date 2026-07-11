from fastapi import APIRouter

from app.api.endpoints import charity_project, donation, user, yandex_api

main_router = APIRouter()
main_router.include_router(
    charity_project.router,
    prefix='/charity_project',
    tags=['charity_projects'],
)
main_router.include_router(
    donation.router,
    prefix='/donation',
    tags=['donations'],
)
main_router.include_router(
    yandex_api.router,
    prefix='/yandex',
    tags=['Yandex Disk'],
)
main_router.include_router(user.router)
