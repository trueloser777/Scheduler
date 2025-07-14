from logging import Logger
import logging
from typing import Final

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database import Database
from database.models.user import User

router: Final[Router] = Router(name=__name__)
logger: Final[Logger] = logging.getLogger(__name__)


@router.message(Command('help'))
async def help_handler(
    message: Message,
    user: User,
    first_seen: bool,
    args: list[str],
    database: Database
):
    await message.reply(
        '<b>Полный список команд бота</b>\n'
        '/preferences - личные настройки пользователя (в каком формате лучше отправлять расписание, за сколько до события отправлять уведомление)\n\n'
        '/today - получить расписание на сегодня. Эквивалент <code>/events 1d 0d</code>\n'
        '/tomorrow - получить расписание на завтра. Эквивалент <code>/events 1d 1d</code>\n'
        '/week - получить расписание на неделю. Эквивалент <code>/events 1w</code>\n'
        '/events &lt;сколько_дней&gt; &lt;начиная_через&gt; - техническая команда для получения расписания с определенными параметрами\n\n'
        'Добавить новое событие Вы можете так:\n'
        '<code>/add [название] [дата] [время]\n'
        '[описание]</code>'
    )
