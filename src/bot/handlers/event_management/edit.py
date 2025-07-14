from logging import Logger
import logging
from typing import Final

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database.models.user import User

router: Final[Router] = Router(name=__name__)
logger: Final[Logger] = logging.getLogger(__name__)


@router.message(Command('edit'))
@router.callback_query(Command('edit'))
async def edit_handler(
    message: Message,
    user: User,
    first_seen: bool
):
    await message.reply(
        f'/start message, first interaction: {first_seen} | is_admin: {user.is_admin}'
    )
