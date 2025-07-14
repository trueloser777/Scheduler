from typing import TYPE_CHECKING, Optional

import asyncpg

from .repositories import (
    Subscriptions, EventTypes, Events, Users,
    UsersPreferences, NotificationsLog
)


class Database:
    if TYPE_CHECKING:
        __host: str
        __port: int
        __user: str
        __password: str
        __database_name: str

        __min_pool_size: int
        __max_pool_size: int

        __pool: asyncpg.Pool | None
    
    if TYPE_CHECKING:
        subscriptions: Subscriptions
        users: Users
        events: Events
        event_types: EventTypes
        user_preferences: UsersPreferences
        notification_logs: NotificationsLog

    def __init__(
            self,
            host: str,
            port: int,
            user: str,
            password: str,
            database_name: str,
            pool: Optional[asyncpg.Pool] = None
    ) -> None:
        self.__host = host
        self.__port = port
        self.__user = user
        self.__password = password
        self.__database_name = database_name

        self.__pool = pool

        self.__min_pool_size = 1
        self.__max_pool_size = 5

        self.subscriptions = Subscriptions()
        self.users = Users()
        self.events = Events()
        self.event_types = EventTypes()
        self.user_preferences = UsersPreferences()
        self.notification_logs = NotificationsLog()

    async def shutdown(self) -> None:
        if not self.__pool:
            return

        await self.__pool.close()

    async def connect(self) -> None:
        if self.__pool:
            return

        self.__pool = await asyncpg.create_pool(
            host=self.__host,
            port=self.__port,
            user=self.__user,
            password=self.__password,
            database=self.__database_name,
            min_size=self.__min_pool_size,
            max_size=self.__max_pool_size
        )

    async def initialize(self) -> None:
        await self.connect()
        
        for repository in [
            self.subscriptions, self.users, 
            self.events, self.event_types,
            self.user_preferences, self.notification_logs
        ]:
            repository.set_pool(self.__pool)
            await repository.initialize()
