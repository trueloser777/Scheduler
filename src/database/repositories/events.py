from datetime import datetime
from ..models.event import *
from ._repository import Repository


class Events(Repository):
    async def create(
            self,
            data: EventCreate
    ) -> Event | None:
        update_data = data.model_dump(exclude_unset=True)
        
        keys = ', '.join(update_data.keys())
        values = ', '.join([
            '${}'.format(i)
            for i in range(
                1, len(update_data.keys()) + 1
            )
        ])

        query = (
            f'INSERT INTO events({keys})'
            f'   VALUES({values})'
            f'   RETURNING *'
        )

        args = list(update_data.values())

        return self._map_record_to_model(
            await self._execute_fetchrow(query, *args),
            Event
        )
    
    async def update(
            self,
            event_id: int,
            data: EventUpdate
    ) -> Event | None:
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise ValueError("No update data provided.")

        set_clauses = [f'{key} = ${i+1}' for i, key in enumerate(update_data.keys())]
        args = list(update_data.values())

        args.append(event_id)
        set_query = ', '.join(set_clauses)
        
        query = (
            f'UPDATE events'
            f'   SET {set_query}'
            f'   WHERE id = ${len(args)}'
            f'   RETURNING *'
        )

        return self._map_record_to_model(
            await self._execute_fetchrow(query, *args),
            Event
        )

    async def by_type_ids(
            self,
            event_type_ids: list[int],
            start_from: datetime,
            end_at: datetime
    ) -> list[Event]:
        """
            :param start_from: Начало временного диапазона для поиска.
            :param end_at: Конец временного диапазона для поиска.
        """
        if not event_type_ids:
            return []

        query = (
            'SELECT *'
            '   FROM events'
            '   WHERE'
            '      event_type_id = ANY($1)'
            '      AND starts_at >= $2'
            '      AND starts_at <= $3'
            '   ORDER BY starts_at ASC'
        )

        args = [event_type_ids, start_from, end_at]

        return self._map_record_list_to_model(
            await self._execute_fetch(query, *args),
            Event
        )

    async def get_ongoing(self) -> list[Event]:
        query = (
            'SELECT *'
            '   FROM events'
            '   WHERE'
            '      starts_at - CURRENT_TIMESTAMP <= INTERVAL \'6 hours\''
        )

        args = []

        return self._map_record_list_to_model(
            await self._execute_fetch(query, *args),
            Event
        )
