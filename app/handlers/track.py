from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.states.track import TrackState

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.track import TrackService

from app.services.user import UserService


router = Router()


@router.message(Command("track"))
async def track_start(
    message: Message,
    state: FSMContext,
) -> None:
    await state.set_state(
        TrackState.waiting_origin
    )

    await message.answer(
        "Введите город отправления:"
    )

@router.message(TrackState.waiting_origin)
async def process_origin(
    message: Message,
    state: FSMContext,
) -> None:
    await state.update_data(
        origin=message.text
    )

    await state.set_state(
        TrackState.waiting_destination
    )

    await message.answer(
        "Введите город назначения:"
    )

@router.message(TrackState.waiting_destination)
async def process_destination(
    message: Message,
    state: FSMContext,
) -> None:
    await state.update_data(
        destination=message.text
    )

    await state.set_state(
        TrackState.waiting_date
    )

    await message.answer(
        "Введите дату вылета (YYYY-MM-DD):"
    )

@router.message(TrackState.waiting_date)
async def process_date(
    message: Message,
    state: FSMContext,
    ) -> None:

    departure_date = date.fromisoformat(
        message.text
    )

    await state.update_data(
        departure_date=departure_date
    )

    await state.set_state(
        TrackState.waiting_target_price
    )

    await message.answer(
        "Введите желаемую цену в рублях.\n\n"
        "Например:\n"
        "15000\n\n"
        'Или отправьте "-" для отслеживания любых изменений цены.'
    )

@router.message(TrackState.waiting_target_price)
async def process_target_price(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:

    data = await state.get_data()

    target_price: int | None = None

    if message.text != "-":
        target_price = int(message.text)

    service = TrackService(session)

    user_service = UserService(session)

    user = await user_service.get_by_telegram_id(
        message.from_user.id
    )

    await service.create_track(
        user_id=user.id,
        origin=data["origin"],
        destination=data["destination"],
        departure_date=data["departure_date"],
        target_price=target_price,
    )

    await state.clear()

    await message.answer(
        "Отслеживание создано! ✈️"
    )