import io
from datetime import datetime, timedelta

import xlsxwriter

from app.core.config import settings
from app.core.yandex_client import YandexDiskClient
from app.models.charity_project import CharityProject

SECONDS_IN_HOUR = 3600
SECONDS_IN_MINUTE = 60
SHEET_NAME = 'Отчёт'
COLUMNS = ('Название проекта', 'Время сбора', 'Описание')
FILENAME_TEMPLATE = 'Отчёт от {date}.xlsx'
REPORT_TITLE_TEMPLATE = 'Отчёт от {date}'
TOTAL_LABEL = 'Итого проектов:'
DAYS_HOURS_TEMPLATE = '{days} дн. {hours} ч.'
HOURS_MINUTES_TEMPLATE = '{hours} ч. {minutes} мин.'
HEADER_BG_COLOR = '#D7E4BC'
FIRST_DATA_ROW = 2
NAME_COLUMN, DURATION_COLUMN, DESCRIPTION_COLUMN = 0, 1, 2
MAX_TABLE_ROWS = 1048576
MAX_TABLE_COLUMNS = 16384
SERVICE_ROWS = 3  # заголовок отчёта, шапка таблицы и итоговая строка
TABLE_SIZE_ERROR = (
    'Отчёт не помещается в таблицу: '
    'требуется строк — {rows} (лимит {max_rows}), '
    'колонок — {columns} (лимит {max_columns}).'
)


def format_time_delta(delta: timedelta) -> str:
    """Представить timedelta строкой с днями, часами и минутами."""
    hours, seconds = divmod(delta.seconds, SECONDS_IN_HOUR)
    minutes = seconds // SECONDS_IN_MINUTE
    if delta.days:
        return DAYS_HOURS_TEMPLATE.format(days=delta.days, hours=hours)
    return HOURS_MINUTES_TEMPLATE.format(hours=hours, minutes=minutes)


async def create_simple_report(
        projects: list[CharityProject],
        client: YandexDiskClient,
) -> str:
    """Создать Excel-отчёт, загрузить на Яндекс Диск и опубликовать.

    Проекты сортируются по скорости сбора средств.
    Возвращает публичную ссылку на файл отчёта.
    """
    rows_required = len(projects) + SERVICE_ROWS
    if rows_required > MAX_TABLE_ROWS or len(COLUMNS) > MAX_TABLE_COLUMNS:
        raise ValueError(TABLE_SIZE_ERROR.format(
            rows=rows_required,
            max_rows=MAX_TABLE_ROWS,
            columns=len(COLUMNS),
            max_columns=MAX_TABLE_COLUMNS,
        ))
    projects = sorted(
        projects,
        key=lambda project: project.close_date - project.create_date,
    )
    report_date = datetime.now().strftime(settings.report_format)
    upload_url, disk_path = await client.create_excel_file(
        FILENAME_TEMPLATE.format(date=report_date)
    )

    buffer = io.BytesIO()
    workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
    worksheet = workbook.add_worksheet(SHEET_NAME)
    title_format = workbook.add_format({'bold': True, 'border': 1})
    header_format = workbook.add_format(
        {'bold': True, 'bg_color': HEADER_BG_COLOR, 'border': 1}
    )
    cell_format = workbook.add_format({'border': 1})

    worksheet.write(
        0, 0, REPORT_TITLE_TEMPLATE.format(date=report_date), title_format
    )
    for column, header in enumerate(COLUMNS):
        worksheet.write(1, column, header, header_format)
    row = FIRST_DATA_ROW
    for project in projects:
        worksheet.write(row, NAME_COLUMN, project.name, cell_format)
        worksheet.write(
            row,
            DURATION_COLUMN,
            format_time_delta(project.close_date - project.create_date),
            cell_format,
        )
        worksheet.write(
            row, DESCRIPTION_COLUMN, project.description, cell_format
        )
        row += 1
    worksheet.write(row, NAME_COLUMN, TOTAL_LABEL, title_format)
    worksheet.write(row, DURATION_COLUMN, len(projects), cell_format)
    workbook.close()

    buffer.seek(0)
    await client.upload_file(upload_url, buffer.read())
    return await client.publish_file(disk_path)
