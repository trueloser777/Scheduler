import datetime

from pydantic import (
    BaseModel, ConfigDict
)


class NotificationLogBase(BaseModel):
    user_id: int
    event_id: int


class NotificationLogCreate(NotificationLogBase):
    pass


class NotificationLog(NotificationLogBase):
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    'NotificationLog',
    'NotificationLogCreate',
]