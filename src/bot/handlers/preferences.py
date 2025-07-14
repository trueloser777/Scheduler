from logging import Logger
import logging
from typing import Final
from datetime import timedelta

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import Database
from database.models.user import User
from database.models.user_preferences import UserPreferencesCreate, UserPreferencesUpdate 

from bot.states.preferences import Preferences


router: Final[Router] = Router(name=__name__)
logger: Final[Logger] = logging.getLogger(__name__)

bot_id = None


async def generate_preferences_keyboard(
        user: User,
        database: Database
) -> InlineKeyboardMarkup | None:
    user_preferences = await database.user_preferences.by_user_id(
        user_id=user.id
    )
    if not user_preferences:
        user_preferences = await database.user_preferences.create(UserPreferencesCreate(
            user_id=user.id
        ))
        if not user_preferences:
            return None

    keyboard = [
        [InlineKeyboardButton(
            text='Изменить время отправки напоминаний',
            callback_data='preferences:change_notifications_interval')]
    ]

    keyboard.append([InlineKeyboardButton(
        text=('🟢' if user_preferences.graphic_schedule else '🔴') + ' Список событий в виде картинки',
        callback_data=f'preferences.set:graphic_schedule:{not user_preferences.graphic_schedule}'
    )])

    keyboard.append([InlineKeyboardButton(
        text=('🟢' if user_preferences.text_schedule else '🔴') + ' Список событий в виде текста',
        callback_data=f'preferences.set:text_schedule:{not user_preferences.text_schedule}'
    )])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.message(Command('preferences'))
@router.callback_query(F.data == 'preferences')
async def preferences_handler(
    event: Message | CallbackQuery,
    user: User,
    database: Database,
    state: FSMContext
):
    global bot_id
    
    await state.clear()

    message = event if isinstance(event, Message) else event.message
    if not bot_id:
        if not event.bot:
            await event.answer(
                '😢 Произошла внутренняя ошибка.\n'
                'Попробуйте еще раз, если не получается - обратитесь к владельцу.'
            )
            return

        bot_id = (await event.bot.get_me()).id
    
    if not message or not isinstance(message, Message):
        if isinstance(event, CallbackQuery):
            await event.answer(
                '😢 Не удалось получить сообщение, на которое надо отвечать.\n'
                'Попробуйте еще раз, если не получается - обратитесь к владельцу.'
            )
        return

    action = message.reply
    if isinstance(event, CallbackQuery) or (message.from_user and message.from_user.id == bot_id):
        action = message.edit_text

    await action(
        text='⚙️ Настройки',
        reply_markup=await generate_preferences_keyboard(
            database=database,
            user=user
        )
    )


@router.callback_query(F.data.startswith('preferences.set:'))
async def preferences_toggle_handler(
    query: CallbackQuery,
    user: User,
    database: Database,
    args: list[str]
):
    if len(args) != 2:
        await query.answer("Ошибка: неверные данные колбэка.", show_alert=True)
        return

    set_what, set_value_str = args
    set_value = set_value_str.lower() == 'true'

    update = UserPreferencesUpdate()
    setattr(update, set_what, set_value)
    if not hasattr(update, set_what):
        logger.error(f"Attempt to set non-existent preference '{set_what}' for user {user.id}")
        await query.answer("Ошибка: неизвестная настройка.", show_alert=True)
        return
    
    await database.user_preferences.update(
        user_id=user.id, 
        data=update
    )
    await query.answer(f"Настройка '{set_what}' изменена!")

    if isinstance(query.message, Message):
        await query.message.edit_reply_markup(
            reply_markup=await generate_preferences_keyboard(user=user, database=database)
        )
    else:
        await query.answer(
            'Не удалось отредактировать сообщение, но настройки были изменены.',
            show_alert=True
        )


@router.callback_query(F.data == 'preferences:change_notifications_interval')
async def change_notifications_interval_handler(
        query: CallbackQuery,
        state: FSMContext
):
    await query.answer()

    if not isinstance(query.message, Message):
        await query.answer(
            'Не удалось отредактировать сообщение, попробуйте заново.',
            show_alert=True
        )
        return

    await query.message.edit_text(
        "Пожалуйста, введите новый интервал для напоминаний в формате <b>ЧЧ:ММ</b>.\n\n"
        "Например: <code>01:30</code> (полтора часа).\n"
        "Максимальное значение: <b>06:00</b>.\n\n"
        "Чтобы вернуться назад, нажмите /preferences."
    )

    await state.set_state(Preferences.waiting_for_time)


@router.message(Preferences.waiting_for_time, F.text)
async def process_time_handler(
        message: Message, 
        state: FSMContext, 
        user: User, 
        database: Database
):
    message_text = message.text or message.caption
    if not message_text:
        await message.reply(
            '😢 Не удалось достать текст из сообщения.\n'
            'Убедитесь, что вы не отправляете его вместе с фото или документами, и попробуйте снова.'
        )
        return

    try:
        parts = message_text.split(':')
        if len(parts) != 2:
            raise ValueError("Неверный формат. Ожидается ЧЧ:ММ.")

        hours, minutes = map(int, parts)

        if not (0 <= hours <= 6 and 0 <= minutes <= 59):
            raise ValueError("Часы должны быть от 0 до 6, минуты от 0 до 59.")

        if hours == 4 and minutes != 0:
            raise ValueError("Максимальное значение - 6 часов (06:00).")

        new_interval = timedelta(hours=hours, minutes=minutes)
        await database.user_preferences.update(
            user_id=user.id,
            data=UserPreferencesUpdate(
                notification_interval=new_interval
            )
        )

        await message.answer(
            f"✅ Интервал напоминаний успешно изменен на <b>{hours:02}:{minutes:02}</b>."
        )


        await state.clear()
        
        await message.answer(
            '⚙️ Настройки',
            reply_markup=await generate_preferences_keyboard(
                database=database,
                user=user
            )
        )

    except (ValueError, TypeError) as e:
        await message.reply(
            f"❌ Ошибка: {e}\n\n"
            "Попробуйте еще раз. Введите время в формате <b>ЧЧ:ММ</b> (например, <code>02:30</code>) или вернитесь в /preferences."
        )
        # Leave user in the same state to let them try again