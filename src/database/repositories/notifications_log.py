from ..models.notification_log import *
from ._repository import Repository


class NotificationsLog(Repository):
    async def create(
            self,
            data: NotificationLogCreate
    ) -> NotificationLog | None:
        update_data = data.model_dump(exclude_unset=True)

        keys = ', '.join(update_data.keys())
        values = ', '.join([
            f'${i}'
            for i in range(
                1, len(update_data.keys()) + 1
            )
        ])

        query = (
            f'INSERT INTO notifications_log({keys})'
            f'   VALUES({values})'
            f'   ON CONFLICT (user_id, event_id) DO NOTHING'
            f'   RETURNING *'
        )

        args = list(update_data.values())

        return self._map_record_to_model(
            await self._execute_fetchrow(query, *args),
            NotificationLog
        )

    async def by_user_id_and_event_id(
            self,
            user_id: int,
            event_id: int
    ) -> NotificationLog | None:
        query = (
            'SELECT *'
            '   FROM notifications_log'
            '   WHERE'
            '      user_id = $1'
            '      AND event_id = $2'
        )

        args = [user_id, event_id]

        return self._map_record_to_model(
            await self._execute_fetchrow(query, *args),
            NotificationLog
        )
