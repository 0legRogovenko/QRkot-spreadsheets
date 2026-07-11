from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Integer
from sqlalchemy.orm import declared_attr

from app.core.db import Base


class CharityBase(Base):
    """Общие поля для целевых проектов и пожертвований."""

    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (
            CheckConstraint(
                'full_amount > 0',
                name='check_full_amount_positive',
            ),
            CheckConstraint(
                '0 <= invested_amount <= full_amount',
                name='check_invested_amount_in_range',
            ),
        )

    full_amount = Column(Integer, nullable=False)
    invested_amount = Column(Integer, nullable=False, default=0)
    fully_invested = Column(Boolean, nullable=False, default=False)
    create_date = Column(DateTime, nullable=False, default=datetime.now)
    close_date = Column(DateTime)

    def __init__(self, **kwargs):
        kwargs.setdefault('invested_amount', 0)
        super().__init__(**kwargs)

    def close_if_fully_invested(self) -> None:
        """Закрыть объект, если собрана вся требуемая сумма."""
        if self.invested_amount == self.full_amount:
            self.fully_invested = True
            self.close_date = datetime.now()

    def __repr__(self):
        return '{}, собрано {} из {}, создано {}, закрыто {}'.format(
            super().__repr__(),
            self.invested_amount,
            self.full_amount,
            self.create_date,
            self.close_date,
        )
