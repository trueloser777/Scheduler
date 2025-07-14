from collections.abc import Iterable
from datetime import datetime, timedelta
from html import escape
from itertools import groupby
from random import choice
import logging
from typing import Final

from database.models.event import Event

logger: Final[logging.Logger] = logging.getLogger(__name__)


DATE_FORMAT = '%d.%m.%Y'
WEEK_DAYS = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']

DAY_SEPARATOR = '⠒⠒⠒⠒⠒⠒⠒⠒⠒⠒⠒⠒⠒⠒⠒⠒⠒⠒'

EVENT_MARKER = '●'
EVENT_EMOJIS = ['🔹', '🔸']
NO_EVENT_EMOJIS = ['🍃', '🏖', '🏝', '🥳', '🎉', '✨']
NO_EVENT_TEXTS = ['Свободный день', 'Нет запланированных мероприятий']


def _format_day_events(events: Iterable[Event]) -> list[str]:
    lines = []
    for event in events:
        title = escape(event.title)
        description = escape(event.description) if event.description else ''

        time_str = event.starts_at.strftime('%H:%M')
        if event.duration:
            end_time = event.starts_at + event.duration
            time_str += ' - ' + end_time.strftime('%H:%M')

        lines.append(f'  {EVENT_MARKER} <code>[{time_str}]</code> <b>{title}</b>')
        if description:
            lines.append(f'    └─ <i>{description}</i>')
        
    return lines


def generate_schedule_text(
        events: list[Event],
        start_date: datetime,
        end_date: datetime
) -> str:
    events.sort(key=lambda e: e.starts_at)
    events_by_day = {
        key: list(group)
        for key, group in groupby(events, key=lambda e: e.starts_at.date())
    }

    schedule_lines = []
    current_date = start_date

    while current_date < end_date:
        day_events = events_by_day.get(current_date.date(), [])
        
        day_of_week_str = WEEK_DAYS[current_date.weekday()]
        date_str = current_date.strftime('%d.%m')
        
        # --- Заголовок и разделитель ---
        header = f'<b>🗓 {day_of_week_str}, {date_str}</b>'
        schedule_lines.append(header)
        schedule_lines.append(DAY_SEPARATOR)
        
        if not day_events:
            emoji = choice(NO_EVENT_EMOJIS)
            text = choice(NO_EVENT_TEXTS)
            event_lines = [f'  {emoji} <i>{text}</i>']
        else:
            event_lines = _format_day_events(day_events)
        
        schedule_lines.extend(event_lines)
        schedule_lines.extend('' for _ in range(2))  # Additional newlines
        current_date += timedelta(days=1)

    return '\n'.join(schedule_lines)
