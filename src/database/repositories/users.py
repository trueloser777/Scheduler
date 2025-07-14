from ..models.user import *
from ._repository import Repository


class Users(Repository):
    async def create(
            self,
            data: UserCreate
    ) -> User | None:
        update_data = data.model_dump(exclude_unset=True)
        
        keys = ', '.join(update_data.keys())
        values = ', '.join([
            '${}'.format(i)
            for i in range(
                1, len(update_data.keys()) + 1
            )
        ])

        query = (
            f'INSERT INTO users({keys})'
            f'   VALUES({values})'
            f'   RETURNING *'
        )

        args = list(update_data.values())

        return self._map_record_to_model(
            await self._execute_fetchrow(query, *args),
            User
        )
    
    async def update(
            self,
            user_id: int,
            data: UserUpdate
    ) -> User | None:
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise ValueError("No update data provided.")

        set_clauses = [f'{key} = ${i+1}' for i, key in enumerate(update_data.keys())]
        args = list(update_data.values())

        args.append(user_id)
        set_query = ', '.join(set_clauses)
        
        query = (
            f'UPDATE users'
            f'   SET {set_query}'
            f'   WHERE id = ${len(args)}'
            f'   RETURNING *'
        )

        return self._map_record_to_model(
            await self._execute_fetchrow(query, *args),
            User
        )
    
    async def by_telegram_id(self, telegram_id: int) -> User | None:
        query = (
            'SELECT *'
            '   FROM users'
            '   WHERE telegram_id = $1'
        )

        args = [telegram_id]

        return self._map_record_to_model(
            await self._execute_fetchrow(query, *args),
            User
        )

    async def by_id(self, user_id: int) -> User | None:
        query = (
            'SELECT *'
            '   FROM users'
            '   WHERE id = $1'
        )

        args = [user_id]

        return self._map_record_to_model(
            await self._execute_fetchrow(query, *args),
            User
        )
