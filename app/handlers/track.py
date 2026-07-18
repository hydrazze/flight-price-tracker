from datetime import date

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.states.track import TrackState

from app.utils.date_parser import parse_date

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.track import TrackService
from app.services.user import UserService

from app.services.city_resolver import resolver


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
        "✈️ Введите город отправления:"
    )



@router.callback_query(
    lambda c: c.data == "create_track"
)
async def create_track_button(
    callback: CallbackQuery,
    state: FSMContext,
):

    await state.set_state(
        TrackState.waiting_origin
    )

    await callback.message.answer(
        "✈️ Введите город отправления:"
    )

    await callback.answer()



@router.message(TrackState.waiting_origin)
async def process_origin(
    message: Message,
    state: FSMContext,
):

    origin = resolver.resolve(
        message.text
    )


    if origin is None:

        await message.answer(
            "❌ Не удалось найти аэропорт.\n\n"
            "Введите город или код аэропорта.\n"
            "Например: Москва или MOW"
        )

        return


    await state.update_data(
        origin=origin
    )


    await state.set_state(
        TrackState.waiting_destination
    )


    await message.answer(
        "🌎 Введите город назначения:"
    )



@router.message(TrackState.waiting_destination)
async def process_destination(
    message: Message,
    state: FSMContext,
):

    destination = resolver.resolve(
        message.text
    )


    if destination is None:

        await message.answer(
            "❌ Не удалось найти такой город."
        )

        return


    await state.update_data(
        destination=destination
    )


    await state.set_state(
        TrackState.waiting_date
    )


    await message.answer(
        "📅 Введите дату вылета:\n\n"
        "Формат: DD-MM-YYYY\n"
        "Например: 30-08-2026"
    )



@router.message(TrackState.waiting_date)
async def process_date(
    message: Message,
    state: FSMContext,
):

    departure_date = parse_date(
        message.text
    )


    if departure_date is None:

        await message.answer(
            "❌ Неверный формат даты."
        )

        return


    if departure_date <= date.today():

        await message.answer(
            "❌ Дата должна быть в будущем."
        )

        return


    await state.update_data(
        departure_date=departure_date
    )


    await state.set_state(
        TrackState.waiting_target_price
    )


    await message.answer(
        "💰 Введите желаемую цену:\n\n"
        "Например: 15000\n\n"
        "Или отправьте '-' чтобы получать любые изменения цены."
    )



@router.message(TrackState.waiting_target_price)
async def process_target_price(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):

    data = await state.get_data()


    target_price = None


    if message.text != "-":

        try:
            target_price = int(
                message.text
            )

        except ValueError:

            await message.answer(
                "❌ Цена должна быть числом."
            )

            return



    service = TrackService(
        session
    )


    user_service = UserService(
        session
    )


    user = await user_service.get_by_telegram_id(
        message.from_user.id
    )


    track = await service.create_track(
        user_id=user.id,
        origin=data["origin"],
        destination=data["destination"],
        departure_date=data["departure_date"],
        target_price=target_price,
    )


    await state.clear()


    if track is None:

        await message.answer(
            "❌ Такое отслеживание уже существует."
        )

        return


    await message.answer(
        "✅ Отслеживание создано! ✈️"
    )