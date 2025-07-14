from logging import Logger, getLogger
from typing import Tuple, Optional

from contextlib import suppress
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.states.event_creation import EventCreation

from database.models.event import EventCreate
from database.models.user import User

from database import Database


router = Router(name=__name__)
logger: Logger = getLogger(__name__)


def _parse_datetime_from_string(
        text: str,
        separator: str = ' '
) -> Tuple[Optional[str], Optional[str]]:
    """Try to parse datetime by guessing the date and time format"""
    parts = text.split(sep=separator)
    date_str, time_str = None, None

    for part in parts:
        guessed_date_format = ''
        if '-' in part:
            # ISO
            guessed_date_format = '%Y-%m-%d'
        elif '.' in part or '/' in part:
            # GOST
            part = part.replace('/', '.')

            # If there is no year, add it, so `%d.%m` will be supported
            if part.count('.') == 1:
                part += f'.{datetime.now().year}'

            guessed_date_format = '%d.%m.%Y'

        # If we haven't guessed the date format, it's most likely not a date, so no need to even bother
        if guessed_date_format:
            with suppress(ValueError):
                parsed = datetime.strptime(part, guessed_date_format)
                date_str = parsed.strftime('%Y-%m-%d')
                continue
        
        # So it _should_ be the time
        with suppress(ValueError):
            datetime.strptime(part, '%H:%M')
            time_str = part

        # If it's not time, then it's nothing to us

    return date_str, time_str


@router.callback_query(F.data.in_({'create.as_private', 'create.as_global'}))
async def process_admin_event_creation_choice(
        callback: CallbackQuery,
        state: FSMContext,
        database: Database,
        user: User
):
    if not callback.message or not isinstance(callback.message, Message):
        await callback.answer('Сообщение не найдено, попробуйте снова.', show_alert=True)
        return

    data = await state.get_data()
    title = data.get('title')
    payload = data.get('payload', 'Отсутствует')
    date_time_str = data.get('date_time_iso')

    if not all([title, date_time_str]):
        await callback.message.edit_text(
            '<b>😢 Данные были повреждены посреди создания события.</b>\n'
            'Придется начать с самого начала :('
        )
        await state.clear()
        return

    date_time = datetime.fromisoformat(date_time_str)  # type: ignore
    event_type = None
    is_global = callback.data == 'create.as_global'

    if is_global:
        event_type = await database.event_types.get_global()
        if not event_type:
            await callback.message.answer(
                '🚫 Не удалось получить глобальный тип событий.\n'
                'Попробуйте снова, если повторится - обратитесь к другому администратору.'
            )
            await state.clear()
            return
    else:  # 'create.as_private'
        event_type = await database.event_types.get_personal_of(user.id)
        if not event_type:
            await callback.message.answer(
                '🚫 Не удалось получить персональный тип событий пользователя.\n'
                'Попробуйте снова, если повторится - обратитесь к администратору.'
            )
            await state.clear()
            return

    await database.events.create(EventCreate(
        title=title,  # type: ignore
        description=payload,
        starts_at=date_time,
        duration=None,
        creator_user_id=user.id,
        event_type_id=event_type.id
    ))

    creation_type_text = "глобальное" if is_global else "приватное"
    text = (
        f'<b>✅ Событие успешно создано как {creation_type_text}!</b>\n\n'
        f'<b>Название</b>: <code>{title}</code>\n'
        f'<b>Дата и время</b>: <code>{date_time.strftime('%d.%m.%Y %H:%M')}</code>\n'
        f'<b>Описание:</b>\n'
        f'<code>{payload}</code>'
    )
    await callback.message.edit_text(text)
    await state.clear()
    await callback.answer()


async def _finalize_event_creation(
        message: Message,
        state: FSMContext,
        date_time: datetime,
        database: Database,
        user: User
):
    data = await state.get_data()
    title = data.get('title')
    payload = data.get('payload', 'Отсутствует')

    if date_time < datetime.now():
        await message.answer(
            '<b>❌ Нельзя создать событие в прошлом.</b>\n'
            'Придется начать с самого начала :('
        )
        await state.clear()
        return

    if (
        not isinstance(title, str)
        or (not isinstance(payload, str) and payload is not None)
    ):
        await message.answer(
            '<b>😢 Данные были побиты посреди создания события.</b>\n'
            'Придется начать с самого начала :('
        )
        await state.clear()
        return

    text = (
        f'<b>Название</b>: <code>{title}</code>\n'
        f'<b>Дата и время</b>: <code>{date_time.strftime('%d.%m.%Y %H:%M')}</code>\n'
        f'<b>Описание:</b>\n'
        f'<code>{payload}</code>'
    )

    if user.is_admin:
        # Сохраняем дату и время в состоянии для их использования в обработчике кнопок
        await state.update_data(date_time_iso=date_time.isoformat())

        text = (
            f'<b>Добавить событие в качестве глобального?</b>\n\n'
            + text
        )

        await message.reply(
            text=text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='🎯 Добавить как приватную', callback_data='create.as_private')],
                [InlineKeyboardButton(text='✅ Добавить как глобальную', callback_data='create.as_global')]
            ])
        )

        return

    text = (
        f'<b>✅ Событие создано!</b>\n\n'
        f'<b>Название</b>: <code>{title}</code>\n'
        f'<b>Дата и время</b>: <code>{date_time.strftime('%d.%m.%Y %H:%M')}</code>'
    )

    if payload and payload != 'Отсутствует':
        text += (
            f'\n<b>Описание</b>:\n'
            f'<code>{payload}</code>'
        )

    personal_event_type = await database.event_types.get_personal_of(user.id)
    if not personal_event_type:
        await message.reply(
            '🚫 Не удалось получить персональный тип событий пользователя.\n'
            'Попробуйте снова, если повторится - обратитесь к администратору.'
        )
        return

    await database.events.create(EventCreate(
        title=title,
        description=payload,
        starts_at=date_time,
        duration=None,
        creator_user_id=user.id,
        event_type_id=personal_event_type.id
    ))
    await message.answer(text)

    await state.clear()


@router.callback_query(F.data == 'create_event')
@router.message(Command('create_event'))
@router.message(Command('add'))
@router.message(Command('add_event'))
async def create_event_handler(
        event: Message | CallbackQuery,
        state: FSMContext,
        database: Database,
        user: User,
        args: Optional[list[str]] = None,
        payload: Optional[str] = None,
):
    if not args or isinstance(event, CallbackQuery):
        if isinstance(event, CallbackQuery):
            message = event.message
        else:
            message = event

        if not message:
            if isinstance(event, CallbackQuery):
                await event.answer('😢 Произошла ошибка: не удалось найти сообщение. Попробуйте снова.', show_alert=True)
            return

        await state.set_state(EventCreation.awaiting_title)
        await message.reply(
            '❔ Введите название события.\n'
            'На следующей строке можно добавить описание, например:\n\n'
            '<code>'
            'ИТ-Раунд\n'
            'ИТ-Раунд — конкурс, проводимый университетом "Сириус", состоит из двух этапов: тестовая часть и проект.\n'
            'И, если первый этап будет сравнительно легким, и ответ на некоторые задания можно угадать, то проектная часть будет чуть сложнее:'
            ' она требует от участника практических знаний в области ИТ. За этот этап можно получить до 50 баллов,'
            ' и это, безусловно, помогает при поступлении в Колледж тем, кто уже имеет опыт в этой сфере, ведь за ИТ-Раунд можно получить вплоть до 10 дополнительных баллов!\n'
            '</code>'
        )
        return

    message = event
    title_parts, date_str, time_str = [], None, None
    for arg in args[::-1]:
        # I'm pretty sure date and time is closer to the back and not to the front
        parsed_date, parsed_time = _parse_datetime_from_string(arg)

        if parsed_date and not date_str:
            date_str = parsed_date
            continue
        elif parsed_time and not time_str:
            time_str = parsed_time
            continue

        title_parts.insert(0, arg)

    title = ' '.join(title_parts)
    if not title:
        await message.reply(
            '<b>❌ Название события не указано.</b>\n'
            'Формат:\n\n'
            '<code>/add [название] [дата] [время]\n'
            '[описание]</code>'
        )
        return

    await state.update_data(
        title=title,
        payload=payload
    )

    if date_str and time_str:
        await _finalize_event_creation(
            message=message,
            state=state,
            date_time=datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M'),
            database=database,
            user=user
        )
        return

    text = f'<b>Название</b>: {title}\n'
    if payload:
        text += '<b>Описание:</b>\n' + payload + '\n\n'

    if not date_str and time_str:
        await state.update_data(time=time_str)
        await state.set_state(EventCreation.awaiting_datetime_parts)

        text += (
            f'<b>Время</b>: {time_str}\n\n'
            f'⚠️ Вы не указали дату. Использовать текущую?'
        )

        await message.reply(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='🎯 Да, это будет сегодня', callback_data='confirm_today')],
                [InlineKeyboardButton(text='🙅 Нет, ввести другую дату', callback_data='enter_another_date')]
            ])
        )
        return

    if date_str and not time_str:
        await state.update_data(date=date_str)
        await state.set_state(EventCreation.awaiting_datetime_parts)

        text += (
            f'<b>Дата</b>: {date_str}\n\n'
            f'⚠️ Вы не ввели время! Отправьте его в формате <code>ЧЧ:ММ</code>.'
        )

        await message.reply(text)
        return

    if not date_str and not time_str:
        await state.set_state(EventCreation.awaiting_datetime_parts)

        text += (
            f'⚠️ Вы не ввели ни даты, ни времени! Отправьте их следующим сообщением.\n'
            f'Например: <code>2025-07-10 14:30</code>'
        )

        await message.reply(text)
        return


@router.message(EventCreation.awaiting_title)
async def process_title(message: Message, state: FSMContext):
    message_text = message.text or message.caption
    if not message_text:
        await message.reply('Пожалуйста, отправьте название в виде текста.')
        return

    message_lines = message_text.split('\n')
    title = message_lines.pop(0)
    description = '\n'.join(message_lines)

    text = f'<b>Название</b>: {title}\n'
    if description:
        text += '<b>Описание:</b>\n' + description + '\n\n'

    text += (
        f'<b>❔ Введите дату и время события</b>\n\n'
        f'<i>Дата может быть в следующих форматах:</i> <code>ГГГГ-ММ-ДД</code>, <code>ДД.ММ.ГГГГ</code>, <code>ДД/ММ/ГГГГ</code>, <code>ДД.ММ</code>, <code>ДД/ММ</code>.\n'
        f'<i>Время может быть только в формате</i> <code>ЧЧ:ММ</code>'
    )

    await message.reply(text)

    await state.update_data(
        title=title,
        payload=description
    )
    await state.set_state(EventCreation.awaiting_datetime_parts)


@router.message(EventCreation.awaiting_datetime_parts, F.text)
async def process_datetime_parts(
        message: Message,
        state: FSMContext,
        database: Database,
        user: User
):
    if not message.text:
        await message.reply(
            '<b>😢 Не удалось достать текст из сообщения!</b>\n'
            'Введите данные повторно, и убедитесь, что Вы не отправляете его вместе с чем-либо еще (изображения, видео, документы).'
        )
        return

    data = await state.get_data()

    parsed_date, parsed_time = _parse_datetime_from_string(message.text)

    # No input check
    if not parsed_date and not parsed_time:
        await message.reply(
            '<b>❌ Не могу распознать ни дату, ни время. Попробуйте еще раз.</b>\n\n'
            '<i>Дата может быть в следующих форматах:</i> <code>ГГГГ-ММ-ДД</code>, <code>ДД.ММ.ГГГГ</code>, <code>ДД/ММ/ГГГГ</code>, <code>ДД.ММ</code>, <code>ДД/ММ</code>.\n'
            '<i>Время может быть только в формате</i> <code>ЧЧ:ММ</code>'
        )
        return

    # Complete input check
    final_date = parsed_date or data.get('date')
    final_time = parsed_time or data.get('time')

    if final_date and final_time:
        try:
            await _finalize_event_creation(
                message=message,
                state=state,
                date_time=datetime.strptime(f'{final_date} {final_time}', '%Y-%m-%d %H:%M'),
                database=database,
                user=user
            )
        except ValueError:
            await message.reply('😢 Произошла ошибка при объединении даты и времени. Пожалуйста, начните заново.')
            await state.clear()

        return

    # Partial input check
    if parsed_date:
        await state.update_data(date=final_date)
        await message.reply(f'✅ Дата выставлена на <code>{final_date}</code>. Осталось ввести время (<code>ЧЧ:ММ</code>).')
        return

    if parsed_time:
        await state.update_data(time=final_time)
        await message.reply(
            f'✅ Время выставлено на <code>{final_time}</code>. Теперь надо ввести дату (<code>ГГГГ-ММ-ДД</code>).',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='🕐 Оно будет сегодня', callback_data='confirm_today')]
            ])
        )
        return


@router.callback_query(F.data.in_({'confirm_today', 'enter_another_date'}))
async def process_callbacks(
        callback: CallbackQuery,
        state: FSMContext,
        database: Database,
        user: User
):
    if not callback.message or not isinstance(callback.message, Message):
        # Should never happen
        if callback.message:
            await callback.message.answer('Оригинальное сообщение было удалено. Необходимо начать с начала.')
        else:
            await callback.answer(
                'Оригинальное сообщение было удалено. Необходимо начать с начала.',
                show_alert=True
            )

        await state.clear()
        return

    await callback.message.edit_reply_markup(reply_markup=None)

    data = await state.get_data()
    title = data.get('title', None)
    time = data.get('time', None)
    if not title or not time:
        cannot_get_what = 'название' if not title else 'время'

        if callback.message:
            await callback.message.edit_text(
                f'😢 Не удалось получить {cannot_get_what} текущего события.\n'
                f'Возможно, событие уже было добавлено? Если нет, попробуйте повторно.'
            )
        else:
            await callback.answer(
                f'😢 Не удалось получить {cannot_get_what} текущего события.\n'
                f'Возможно, событие уже было добавлено? Если нет, попробуйте повторно.',
                show_alert=True
            )

        return

    if callback.data == 'confirm_today':
        date_str = datetime.now().strftime('%Y-%m-%d')
        await _finalize_event_creation(
            message=callback.message,
            state=state,
            date_time=datetime.strptime(f"{date_str} {data['time']}", '%Y-%m-%d %H:%M'),
            database=database,
            user=user
        )
    elif callback.data == 'enter_another_date':
        await state.set_state(EventCreation.awaiting_datetime_parts)
        await callback.message.edit_text('Введите дату в формате <code>ГГГГ-ММ-ДД</code>.')

    await callback.answer()
