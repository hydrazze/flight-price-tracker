from aiogram.fsm.state import State, StatesGroup


class TrackState(StatesGroup):
    waiting_origin = State()
    waiting_destination = State()
    waiting_date = State()
    waiting_target_price = State()

    editing_target_price = State()