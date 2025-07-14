import datetime

from pydantic import (
    BaseModel, ConfigDict
)


class SubscriptionBase(BaseModel):
    """Базовая модель для подписки."""
    user_id: int
    event_type_id: int


class SubscriptionCreate(SubscriptionBase):
    """Модель для создания новой подписки."""
    pass


class Subscription(SubscriptionBase):
    id: int
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


__all__ = ['Subscription', 'SubscriptionCreate']
