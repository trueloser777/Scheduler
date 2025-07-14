

import asyncpg
from typing import TYPE_CHECKING, Optional, Type, TypeVar
from pydantic import BaseModel


ModelType = TypeVar("ModelType", bound=BaseModel)

class Repository:
    if TYPE_CHECKING:
        _pool: asyncpg.Pool | None

    def __init__(self):
        self._pool = None

    def set_pool(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def initialize(self):
        """
        Shouldn't be used since table creation and all the stuff is made through migrations
        """
        pass

    def _map_record_to_model(
        self,
        record: asyncpg.Record | None,
        model: Type[ModelType]
    ) -> ModelType | None:
        if not record:
            return None

        return model.model_validate(dict(record))

    def _map_record_list_to_model(
            self,
            records: list[asyncpg.Record] | None,
            model: Type[ModelType]
    ) -> list[ModelType]:
        if not records:
            return []

        result = []
        for record in records:
            result.append(self._map_record_to_model(
                record=record,
                model=model
            ))

        return result

    async def __execute(
        self,
        query: str,
        *args,
        fetch: bool = False,
        fetchval: bool = False,
        fetchrow: bool = False,
        executemany: bool = False,
    ) -> Optional[asyncpg.Record | list[asyncpg.Record]]:
        if not self._pool:
            raise RuntimeError('Tried to call _execute without _pool')
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                if executemany:
                    await conn.executemany(query, args[0])
                    return None

                if fetch:
                    return await conn.fetch(query, *args)

                if fetchval:
                    return await conn.fetchval(query, *args)

                if fetchrow:
                    return await conn.fetchrow(query, *args)

                await conn.execute(query, *args)
                return None
    
    async def _execute_fetch(self, *args, **kwargs) -> list[asyncpg.Record]:
        result = await self.__execute(*args, **kwargs, fetch=True)
        if not isinstance(result, list):
            return []

        return result
    
    async def _execute_fetchrow(self, *args, **kwargs) -> asyncpg.Record | None:
        result = await self.__execute(*args, **kwargs, fetchrow=True)
        if not isinstance(result, asyncpg.Record):
            return None

        return result


__all__ = ['Repository']
