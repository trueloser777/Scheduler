from aiogram.fsm.state import StatesGroup, State


class EventCreation(StatesGroup):
    awaiting_title = State()
    awaiting_datetime_parts = State()
