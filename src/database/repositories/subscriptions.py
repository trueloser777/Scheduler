from ..models.subscription import *
from ._repository import Repository


class Subscriptions(Repository):
    async def create(
            self,
            data: SubscriptionCreate
    ) -> Subscription | None:
        update_data = data.model_dump(exclude_unset=True)
        
        keys = ', '.join(update_data.keys())
        values = ', '.join([
            '${}'.format(i)
            for i in range(
                1, len(update_data.keys()) + 1
            )
        ])

        query = (
            f'INSERT INTO subscriptions({keys})'
            f'   VALUES({values})'
            f'   RETURNING *'
        )

        args = list(update_data.values())

        return self._map_record_to_model(
            await self._execute_fetchrow(query, *args),
            Subscription
        )
    
    async def remove(
            self,
            subscription_id: int
    ) -> None:
        query = (
            'DELETE FROM subscriptions'
            '   WHERE id = $1'
        )

        args = [subscription_id]

        await self._execute_fetchrow(query, *args)

    async def by_user_id(self, user_id: int) -> list[Subscription] | None:
        query = (
            'SELECT *'
            '   FROM subscriptions'
            '   WHERE user_id = $1'
        )

        args = [user_id]

        return self._map_record_list_to_model(
            await self._execute_fetch(query, *args),
            Subscription
        )
    
    async def by_event_type_id(self, event_type_id: int) -> list[Subscription] | None:
        query = (
            'SELECT *'
            '   FROM subscriptions'
            '   WHERE event_type_id = $1'
        )

        args = [event_type_id]

        return self._map_record_list_to_model(
            await self._execute_fetch(query, *args),
            Subscription
        )
