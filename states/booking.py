from aiogram.fsm.state import State, StatesGroup

class BookingStates(StatesGroup):
    """Состояния для процесса записи"""
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_name = State()
    waiting_for_phone = State()
    confirmation = State()