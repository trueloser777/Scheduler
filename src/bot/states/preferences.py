from aiogram.fsm.state import StatesGroup, State


class Preferences(StatesGroup):
    waiting_for_time = State()
