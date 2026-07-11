from app.models.base import CharityBase


def invest(
        target: CharityBase,
        sources: list[CharityBase],
) -> list[CharityBase]:
    """Распределить свободные средства между target и sources.

    target — новый проект или новое пожертвование,
    sources — открытые объекты противоположного типа
    в порядке их создания.
    Возвращает изменённые объекты из sources.
    """
    changed = []
    for source in sources:
        changed.append(source)
        transfer = min(
            target.full_amount - target.invested_amount,
            source.full_amount - source.invested_amount,
        )
        for obj in (target, source):
            obj.invested_amount += transfer
            obj.close_if_fully_invested()
        if target.fully_invested:
            break
    return changed
