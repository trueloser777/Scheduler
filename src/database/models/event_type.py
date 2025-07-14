import datetime
from typing import Optional

from pydantic import (
    BaseModel, ConfigDict,
    Field, model_validator
)


class EventTypeBase(BaseModel):
    title: str = Field(max_length=64)
    description: str = ""
    is_default: bool = False
    is_public: bool = True

    owner_user_id: Optional[int] = None

    @model_validator(mode='after')
    def check_public_or_default(self) -> 'EventTypeBase':
        if not self.is_public and self.is_default:
            raise ValueError("The private event_type cannot be set as the default")

        return self


class EventTypeCreate(EventTypeBase):
    pass


class EventTypeUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=64)
    description: Optional[str] = None
    is_default: Optional[bool] = None
    is_public: Optional[bool] = None

    @model_validator(mode='after')
    def check_public_or_default(self) -> 'EventTypeUpdate':
        if not self.is_public and self.is_default:
            raise ValueError("The private event_type cannot be set as the default")

        return self


class EventType(EventTypeBase):
    id: int
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


__all__ = ['EventType', 'EventTypeUpdate', 'EventTypeCreate']
