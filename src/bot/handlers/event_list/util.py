from datetime import datetime
from logging import Logger
import logging
from typing import Final
import re

from aiogram import Router


router: Final[Router] = Router(name=__name__)
logger: Final[Logger] = logging.getLogger(__name__)


DATE_FORMAT = '%d.%m.%Y'

TIME_UNIT_TO_DAYS: Final[dict[str, int]] = {
    # English
    'd': 1, 'day': 1, 'days': 1,
    'w': 7, 'week': 7, 'weeks': 7,
    'm': 30, 'mo': 30, 'month': 30, 'months': 30,
    # Russian
    'д': 1, 'дн': 1, 'дня': 1, 'дней': 1, 'день': 1,
    'н': 7, 'нед': 7, 'неделя': 7, 'недель': 7,
    'м': 30, 'мес': 30, 'месяц': 30, 'месяцев': 30,
}

TIME_UNITS_PATTERN: Final[str] = '|'.join(TIME_UNIT_TO_DAYS.keys())
TIME_EXTRACTION_PATTERN: Final[re.Pattern] = re.compile(rf'(\d+)\s*({TIME_UNITS_PATTERN})')


def convert_to_days(value: int, unit: str) -> int:
    unit_in_days = TIME_UNIT_TO_DAYS.get(unit.lower(), 0)
    return value * unit_in_days


def get_period_string(
        start_date: datetime, 
        end_date: datetime,
        interval: int,
        offset: int
) -> str:
    start_date_str = start_date.strftime(DATE_FORMAT)
    end_date_str = end_date.strftime(DATE_FORMAT)
    
    if interval == 1:
        if offset == 0:
            period_str = 'на сегодня'
        elif offset == 1:
            period_str = 'на завтра'
        else:
            period_str = f'на {start_date_str}'
    else:
        period_str = f'с {start_date_str} по {end_date_str}'

    return period_str


def gather_interval(text: str) -> tuple[int, int]:
    # Extract both the interval and offset from the message
    # It may be today, tomorrow, week, month (the command itself)
    # Also it may be /events 1d, /events 1m 1d, /events 1mo, etc
    # First occurrence is the interval, second occurrence is the offset
    # So it should work like that:
    #   '7d 1w' -> get 7 days of events starting after a week
    #   '10d' -> get 10 days starting from today
    simple_cases = {
        'today': (1, 0),
        'tomorrow': (1, 1),
        '/week': (7, 0),
        '/month': (30, 0),
    }
    for keyword, result in simple_cases.items():
        if keyword in text:
            return result

    matches = TIME_EXTRACTION_PATTERN.findall(text)
    if not matches:
        return 1, 0

    interval_val_str, interval_unit = matches[0]
    interval_days = convert_to_days(int(interval_val_str), interval_unit)

    offset_days = 0

    if len(matches) > 1:
        offset_val_str, offset_unit = matches[1]
        offset_days = convert_to_days(int(offset_val_str), offset_unit)

    return (interval_days, offset_days)


__all__ = ['gather_interval', 'get_period_string', 'convert_to_days']
