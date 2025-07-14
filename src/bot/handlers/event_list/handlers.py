from datetime import datetime, timedelta
from logging import Logger
import logging
from typing import Final

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types import BufferedInputFile


from .util import *
from .image_list import generate_schedule_image
from .text_list import generate_schedule_text

from database.models.user import User

from database import Database


router: Final[Router] = Router(name=__name__)
logger: Final[Logger] = logging.getLogger(__name__)


@router.message(Command('today'))
@router.message(Command('tomorrow'))
@router.message(Command('week'))
@router.message(Command('events'))
async def events_list_handler(
    message: Message,
    user: User,
    database: Database
):
    message_text = message.text or message.caption
    if not message_text:
        await message.reply(
            '❌ В сообщении нету текста.\n'
            'Это не должно было произойти, но это произошло. Попробуйте еще раз.'
        )
        return

    interval, offset = gather_interval(message_text)

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    start_date = today + timedelta(days=offset)
    end_date = start_date + timedelta(days=interval)

    period_str = get_period_string(
        start_date=start_date,
        end_date=end_date,
        interval=interval,
        offset=offset
    )

    user_subscriptions = await database.subscriptions.by_user_id(user.id)
    if not user_subscriptions:
        # Shouldn't happen, since the user have to be subscribed to at least his own events
        # Otherwise something really bad happened
        await message.reply('ℹ️ Вы не подписаны ни на один из видов событий.')
        return

    user_event_types = list(map(lambda x: x.event_type_id, user_subscriptions))
    events = await database.events.by_type_ids(
        event_type_ids=user_event_types,
        start_from=start_date,
        end_at=end_date
    )

    if not events:
        await message.reply(f'✨ Расписание {period_str} пусто ✨')
        return

    user_preferences = await database.user_preferences.by_user_id(
        user_id=user.id
    )
    if user_preferences:
        if user_preferences.graphic_schedule and not user_preferences.text_schedule:
            await message.reply_photo(
                caption='Расписание в виде фото готово! ✨',
                photo=BufferedInputFile(generate_schedule_image(
                    events=events,
                    start_date=start_date,
                    end_date=end_date
                ).read(), 'schedule.png')
            )
            return

        if user_preferences.text_schedule and not user_preferences.graphic_schedule:
            await message.reply(
                text=generate_schedule_text(
                    events=events,
                    start_date=start_date,
                    end_date=end_date
                )
            )
            return
        
    await message.reply_photo(
        caption=generate_schedule_text(
            events=events,
            start_date=start_date,
            end_date=end_date
        ),
        photo=BufferedInputFile(generate_schedule_image(
            events=events,
            start_date=start_date,
            end_date=end_date
        ).read(), 'schedule.png')
    )
