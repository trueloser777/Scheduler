import datetime
from typing import Optional

from pydantic import (
    BaseModel, ConfigDict
)


class UserBase(BaseModel):
    telegram_id: int
    is_admin: bool = False


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    is_admin: Optional[bool] = None


class User(UserBase):
    id: int
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


__all__ = ['User', 'UserUpdate', 'UserCreate']
