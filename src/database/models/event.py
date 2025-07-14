import datetime
from typing import Optional

from pydantic import (
    BaseModel, ConfigDict,
    Field, field_validator
)


class EventBase(BaseModel):
    """Базовая модель для события."""
    title: str = Field(max_length=64)
    description: str = ""

    starts_at: datetime.datetime
    duration: Optional[datetime.timedelta] = None

    @field_validator("duration")
    @classmethod
    def duration_must_be_positive(cls, v: Optional[datetime.timedelta]):
        if v is not None and v.total_seconds() <= 0:
            raise ValueError("Event duration cannot be negative")

        return v


class EventCreate(EventBase):
    creator_user_id: int
    event_type_id: int


class EventUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=64)
    description: Optional[str] = None

    starts_at: Optional[datetime.datetime] = None
    duration: Optional[datetime.timedelta] = None

    @field_validator("duration")
    @classmethod
    def duration_must_be_positive(cls, v: Optional[datetime.timedelta]):
        if v is not None and v.total_seconds() <= 0:
            raise ValueError("Event duration cannot be negative")

        return v


class Event(EventBase):
    id: int
    created_at: datetime.datetime

    event_type_id: int
    creator_user_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


__all__ = ['Event', 'EventUpdate', 'EventCreate']
