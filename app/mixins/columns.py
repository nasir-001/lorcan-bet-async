from datetime import date
from typing import Any
import ulid

import inflect

from sqlalchemy import Column, DateTime, Integer, String, Date
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql.functions import func

get_plural = inflect.engine()


def get_new_ulid() -> str:
    return ulid.new().str


class BaseMixin:
    __allow_unmapped__ = True
    """
    Provides id, created_at and last_modified columns
    """

    @declared_attr  # type: ignore
    def __tablename__(cls: Any) -> str:
        try:
            cls.__tablename__
        except RecursionError:
            pass
        plural_name: str = get_plural.plural_noun(cls.__name__.lower())
        return plural_name

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    uuid = Column(String(length=50), unique=True, nullable=False, default=get_new_ulid)
    date = Column(
        Date,
        index=True,
        default=date.today,
        nullable=True,
        server_default=func.current_date(),
    )
    created_at = Column(DateTime, index=True, server_default=func.now(), nullable=False)
    last_modified = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
