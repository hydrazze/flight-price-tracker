from datetime import date, timedelta

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from app.states.track import TrackState
from app.models.enums import StopPreference
from app.keyboards.trip_options import trip_type_keyboard, stop_preference_keyboard

from app.utils.date_parser import parse_date
from app.utils.track_formatter import format_track

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

    await state.clear()
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

    await state.clear()
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
        f"Например: {(date.today() + timedelta(days=7)).strftime('%d-%m-%Y')}",
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


    await state.set_state(TrackState.waiting_trip_type)
    await message.answer("✈️ Тип поездки", reply_markup=trip_type_keyboard)


@router.callback_query(
    TrackState.waiting_trip_type,
    lambda c: c.data in ("trip:one_way", "trip:round_trip"),
)
async def process_trip_type(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    # Retire the selected keyboard so old choices cannot be clicked again.
    await callback.message.edit_reply_markup(reply_markup=None)
    if callback.data == "trip:round_trip":
        await state.set_state(TrackState.waiting_return_date)
        await callback.message.answer(
            "📅 Введите дату обратного вылета в формате DD-MM-YYYY. "
            "Она должна быть не раньше вылета туда.",
            reply_markup=cancel_keyboard,
        )
    else:
        await state.update_data(return_date=None)
        await ask_stop_preference(callback.message, state)


async def ask_stop_preference(message: Message, state: FSMContext):
    await state.set_state(TrackState.waiting_stop_preference)
    await message.answer(
        "🛫 Предпочтения по пересадкам\n\n"
        "Для поездки туда и обратно «Без пересадок» означает прямые рейсы "
        "в обе стороны, «С пересадками» — пересадку хотя бы в одну сторону.",
        reply_markup=stop_preference_keyboard,
    )


@router.message(TrackState.waiting_return_date)
async def process_return_date(message: Message, state: FSMContext):
    return_date = parse_date(message.text)
    data = await state.get_data()
    if return_date is None or return_date < data["departure_date"]:
        await message.answer(
            "❌ Введите дату DD-MM-YYYY не раньше даты вылета туда.",
            reply_markup=cancel_keyboard,
        )
        return
    await state.update_data(return_date=return_date)
    await ask_stop_preference(message, state)


@router.callback_query(
    TrackState.waiting_stop_preference,
    lambda c: c.data in {f"stops:{p.value}" for p in StopPreference},
)
async def process_stop_preference(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    preference = StopPreference(callback.data.split(":", 1)[1])
    await state.update_data(stop_preference=preference.value)
    await state.set_state(TrackState.waiting_target_price)
    data = await state.get_data()
    price_scope = (
        "за всю поездку туда и обратно"
        if data.get("return_date") else "за перелёт в одну сторону"
    )
    await callback.message.answer(
        f"💰 Введите максимальную цену в рублях {price_scope}.\n\n"
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


        except (TypeError, ValueError):

            await message.answer(
                "❌ Цена должна быть числом.",
                reply_markup=cancel_keyboard,
            )

            return



    if target_price is not None and not 0 < target_price <= 2_147_483_647:
        await message.answer("❌ Введите положительную цену до 2147483647 ₽ или '-'.", reply_markup=cancel_keyboard)
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
        return_date=data.get("return_date"),
        stop_preference=StopPreference(data.get("stop_preference", "any")),
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
        + format_track(track),
        reply_markup=main_keyboard,
    )
