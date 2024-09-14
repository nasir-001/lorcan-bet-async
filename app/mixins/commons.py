from enum import Enum
from pydantic import BaseModel
from datetime import date

class OrderStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


class ListBase(BaseModel):
    count: int


class FilterBase(BaseModel):
    skip: int
    limit: int

class DateRange(BaseModel):
    column_name: str = "date"
    from_date: date
    to_date: date
