import datetime
from typing import Optional

from pydantic import (
    BaseModel, ConfigDict,
    Field, field_validator
)


class UserPreferencesBase(BaseModel):
    user_id: int
    notification_interval: datetime.timedelta = Field(default=datetime.timedelta(hours=1))
    graphic_schedule: bool = True
    text_schedule: bool = True

    @field_validator('notification_interval')
    def check_notification_interval(cls, v: datetime.timedelta) -> datetime.timedelta:
        if v is not None and v > datetime.timedelta(hours=6):
            raise ValueError('The notification_interval must be less than or equal to 6 hours')
        return v


class UserPreferencesCreate(UserPreferencesBase):
    pass


class UserPreferencesUpdate(BaseModel):
    notification_interval: Optional[datetime.timedelta] = None
    graphic_schedule: Optional[bool] = None
    text_schedule: Optional[bool] = None

    @field_validator('notification_interval')
    def check_notification_interval(cls, v: Optional[datetime.timedelta]) -> Optional[datetime.timedelta]:
        if v is not None and v > datetime.timedelta(hours=6):
            raise ValueError('The notification_interval must be less than or equal to 6 hours')
        return v


class UserPreferences(UserPreferencesBase):
    model_config = ConfigDict(from_attributes=True)


__all__ = [
    'UserPreferences',
    'UserPreferencesCreate',
    'UserPreferencesUpdate'
]
