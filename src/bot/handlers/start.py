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


@router.message(Command('schedule'))
@router.message(Command('start'))
async def start_handler(
    message: Message,
    user: User,
    first_seen: bool,
    args: list[str],
    database: Database
):
    await message.reply(
        '👋 Приветствую тебя в боте NamelessScheduler\n'
        'Он был создан 14.07.2025 в рамках конкурса "IT-Раунд", который проводит университет Сириус.\n\n'
        'Полный список команд доступен по /help\n\n'
        'Добавить новое событие Вы можете так:\n'
        '<code>/add [название] [дата] [время]\n'
        '[описание]</code>'
    )
