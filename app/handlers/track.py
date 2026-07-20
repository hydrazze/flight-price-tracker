from datetime import date

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from app.states.track import TrackState

from app.utils.date_parser import parse_date

from app.services.track import TrackService
from app.services.user import UserService
from app.services.city_resolver import resolver

from app.keyboards.cancel import cancel_keyboard
from app.keyboards.main import main_keyboard


router = Router()



async def start_track_creation(
    message: Message,
    state: FSMContext,
):

    await state.set_state(
        TrackState.waiting_origin
    )


    await message.answer(
        "✈️ <b>Новое отслеживание</b>\n\n"
        "Введите город отправления.\n\n"
        "Например:\n"
        "Москва",
        reply_markup=cancel_keyboard,
    )



@router.message(
    Command("track")
)
async def track_start(
    message: Message,
    state: FSMContext,
):

    await start_track_creation(
        message,
        state,
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
        "✈️ <b>Новое отслеживание</b>\n\n"
        "Введите город отправления.\n\n"
        "Например:\n"
        "Москва",
        reply_markup=cancel_keyboard,
    )


    await callback.answer()



@router.message(TrackState.waiting_origin)
async def process_origin(
    message: Message,
    state: FSMContext,
):
    origin = resolver.resolve(message.text)

    if origin is None:
        await message.answer(
            "❌ Не удалось найти аэропорт.\n\n"
            "Введите город или код аэропорта.\n"
            "Например: Москва или MOW",
            reply_markup=cancel_keyboard,
        )
        return

    await state.update_data(
        origin=origin["code"],
        origin_name=origin["city"],
    )

    await state.set_state(TrackState.waiting_destination)

    await message.answer(
        "🌎 <b>Город назначения</b>\n\n"
        "Введите город, куда хотите полететь.",
        reply_markup=cancel_keyboard,
    )



@router.message(TrackState.waiting_destination)
async def process_destination(
    message: Message,
    state: FSMContext,
):
    destination = resolver.resolve(message.text)

    if destination is None:
        await message.answer(
            "❌ Такой город не найден.\n\n"
            "Попробуйте еще раз.",
            reply_markup=cancel_keyboard,
        )
        return

    await state.update_data(
        destination=destination["code"],
        destination_name=destination["city"],
    )

    await state.set_state(TrackState.waiting_date)

    await message.answer(
        "📅 <b>Дата вылета</b>\n\n"
        "Введите дату в формате:\n"
        "DD-MM-YYYY\n\n"
        "Например: 30-08-2026",
        reply_markup=cancel_keyboard,
    )


@router.message(
    TrackState.waiting_date
)
async def process_date(
    message: Message,
    state: FSMContext,
):

    departure_date = parse_date(
        message.text
    )


    if departure_date is None:

        await message.answer(
            "❌ Неверный формат даты.\n\n"
            "Используйте DD-MM-YYYY.",
            reply_markup=cancel_keyboard,
        )

        return



    if departure_date <= date.today():

        await message.answer(
            "❌ Дата должна быть в будущем.",
            reply_markup=cancel_keyboard,
        )

        return



    await state.update_data(
        departure_date=departure_date
    )


    await state.set_state(
        TrackState.waiting_target_price
    )


    await message.answer(
        "💰 <b>Желаемая цена</b>\n\n"
        "Введите максимальную цену в рублях.\n\n"
        "Например: 15000\n\n"
        "Или отправьте «-», чтобы получать любые изменения цены.",
        reply_markup=cancel_keyboard,
    )



@router.message(
    TrackState.waiting_target_price
)
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
                "❌ Цена должна быть числом.",
                reply_markup=cancel_keyboard,
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

    if user is None:
        user = await user_service.get_or_create(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
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
            "❌ Такое отслеживание уже существует.",
            reply_markup=main_keyboard,
        )

        return



    await message.answer(
        "✅ <b>Отслеживание создано!</b>\n\n"
        "Теперь я буду следить за ценой ✈️",
        reply_markup=main_keyboard,
    )