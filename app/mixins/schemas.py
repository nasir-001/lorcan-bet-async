from enum import Enum
from app.utils.enums import ActionStatus
from datetime import datetime, date as dt_date
from typing import Any, Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class BaseSchemaMixin(BaseModel):
    id: int
    uuid: str
    date: dt_date
    created_at: datetime
    last_modified: datetime

    model_config = ConfigDict(from_attributes=True)



class BaseUACSchemaMixin(BaseSchemaMixin):
    name: str
    description: Optional[str]


class JoinSearch(BaseModel):
    model: Any
    column: str
    onkey: str