from ..models.event_type import *
from ._repository import Repository


class EventTypes(Repository):
    async def create(
            self,
            data: EventTypeCreate
    ) -> EventType | None:
        update_data = data.model_dump(exclude_unset=True)
        
        keys = ', '.join(update_data.keys())
        values = ', '.join([
            '${}'.format(i)
            for i in range(
                1, len(update_data.keys()) + 1
            )
        ])

        query = (
            f'INSERT INTO event_types({keys})'
            f'   VALUES({values})'
            f'   RETURNING *'
        )

        args = list(update_data.values())

        return self._map_record_to_model(
            await self._execute_fetchrow(query, *args),
            EventType
        )

    async def update(
            self,
            event_type_id: int,
            data: EventTypeUpdate
    ) -> EventType | None:
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise ValueError("No update data provided.")

        set_clauses = [f'{key} = ${i+1}' for i, key in enumerate(update_data.keys())]
        args = list(update_data.values())

        args.append(event_type_id)
        set_query = ', '.join(set_clauses)
        
        query = (
            f'UPDATE event_types'
            f'   SET {set_query}'
            f'   WHERE id = ${len(args)}'
            f'   RETURNING *'
        )

        return self._map_record_to_model(
            await self._execute_fetchrow(query, *args),
            EventType
        )

    async def get_personal_of(self, user_id: int) -> EventType | None:
        query = (
            'SELECT *'
            '   FROM event_types'
            '   WHERE'
            '      owner_user_id = $1'
            '      AND title = $2'
            '   LIMIT 1'
        )

        args = [user_id, f'Personal {user_id}']

        return self._map_record_to_model(
            await self._execute_fetchrow(query, *args),
            EventType
        )

    async def get_global(self) -> EventType:
        query = (
            'SELECT *'
            '   FROM event_types'
            '   WHERE'
            '      title = \'Default\''
        )

        args = []

        result = self._map_record_to_model(
            await self._execute_fetchrow(query, *args),
            EventType
        )

        if not result:
            raise RuntimeError('Cannot find the default event type')

        return result
