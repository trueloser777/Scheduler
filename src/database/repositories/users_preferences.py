from ..models.user_preferences import *
from ._repository import Repository


class UsersPreferences(Repository):
    async def create(
            self,
            data: UserPreferencesCreate
    ) -> UserPreferences | None:
        update_data = data.model_dump(exclude_unset=True)

        keys = ', '.join(update_data.keys())
        values = ', '.join([
            f'${i}'
            for i in range(
                1, len(update_data.keys()) + 1
            )
        ])

        query = (
            f'INSERT INTO user_preferences({keys})'
            f'   VALUES({values})'
            f'   RETURNING *'
        )

        args = list(update_data.values())

        return self._map_record_to_model(
            await self._execute_fetchrow(query, *args),
            UserPreferences
        )

    async def update(
            self,
            user_id: int,
            data: UserPreferencesUpdate
    ) -> UserPreferences | None:
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise ValueError("No update data provided.")

        set_clauses = [f'{key} = ${i+1}' for i, key in enumerate(update_data.keys())]
        args = list(update_data.values())

        args.append(user_id)
        set_query = ', '.join(set_clauses)

        query = (
            f'UPDATE user_preferences'
            f'   SET {set_query}'
            f'   WHERE user_id = ${len(args)}'
            f'   RETURNING *'
        )

        return self._map_record_to_model(
            await self._execute_fetchrow(query, *args),
            UserPreferences
        )

    async def by_user_id(self, user_id: int) -> UserPreferences | None:
        query = (
            'SELECT *'
            '   FROM user_preferences'
            '   WHERE user_id = $1'
        )

        args = [user_id]

        return self._map_record_to_model(
            await self._execute_fetchrow(query, *args),
            UserPreferences
        )
