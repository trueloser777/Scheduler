from typing import TYPE_CHECKING, Any, Awaitable, Callable, override

from database import Database

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from database.models.user import UserCreate


class CreateUserOnCommand(BaseMiddleware):
    if TYPE_CHECKING:
        __database: Database

    def __init__(
            self,
            database: Database
    ):
        self.__database = database

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        if not isinstance(event, (Message, CallbackQuery)) or not event.from_user:
            return await handler(event, data)

        first_seen = False
        user = await self.__database.users.by_telegram_id(event.from_user.id)
        if not user:
            first_seen = True
            user = await self.__database.users.create(UserCreate(
                telegram_id=event.from_user.id
            ))

        data['database'] = self.__database
        data['user'] = user
        data['first_seen'] = first_seen

        # TODO: Вынести это в отдельный миддлварь
        if isinstance(event, Message) and (event.text or event.caption):
            message_text = event.text or event.caption
            newline_split = message_text.split('\n')  # type: ignore
            args_split = newline_split[0].split(' ')

            data['args'] = args_split[1:]
            data['command'] = args_split[0][1:]

            if len(newline_split) > 1:
                data['payload'] = '\n'.join(newline_split[1:])
            else:
                data['payload'] = ''
        elif isinstance(event, CallbackQuery) and event.data:
            callback_data_split = event.data.split(':')

            data['args'] = callback_data_split[1:]
            data['command'] = callback_data_split[0]
            data['payload'] = ''
        else:
            data['args'] = []
            data['command'] = ''
            data['payload'] = ''

        return await handler(event, data)
