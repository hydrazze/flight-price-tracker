from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from app.models.track import Track
from app.models.enums import StopPreference



def tracks_keyboard(
    tracks: list[Track],
):

    builder = InlineKeyboardBuilder()


    for track in tracks:

        dates = track.departure_date.strftime("%d.%m.%y")
        if track.return_date:
            dates += "–" + track.return_date.strftime("%d.%m.%y")
        arrow = "↔" if track.return_date else "→"
        preference = StopPreference(track.stop_preference or StopPreference.ANY)
        builder.button(
            text=f"{track.origin} {arrow} {track.destination} | {dates} | {preference.label}",
            callback_data=f"track:{track.id}",
        )


    builder.adjust(1)


    builder.row(
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="main_menu",
        )
    )


    return builder.as_markup()



def track_detail_keyboard(
    track_id: int,
):

    builder = InlineKeyboardBuilder()


    builder.row(
        InlineKeyboardButton(
            text="🔄 Проверить сейчас",
            callback_data=f"check_track:{track_id}",
        )
    )


    builder.row(
        InlineKeyboardButton(
            text="🎯 Изменить цель",
            callback_data=f"edit_target_price:{track_id}",
        )
    )


    builder.row(
        InlineKeyboardButton(
            text="📊 История цены",
            callback_data=f"price_history:{track_id}",
        )
    )


    builder.row(
        InlineKeyboardButton(
            text="🗑 Удалить",
            callback_data=f"delete_track:{track_id}",
        )
    )


    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="back_to_tracks",
        )
    )


    builder.row(
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="main_menu",
        )
    )


    return builder.as_markup()



def delete_confirm_keyboard(
    track_id: int,
):

    builder = InlineKeyboardBuilder()


    builder.row(
        InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data=f"confirm_delete:{track_id}",
        )
    )


    builder.row(
        InlineKeyboardButton(
            text="⬅️ Отмена",
            callback_data=f"track:{track_id}",
        )
    )


    return builder.as_markup()



def archive_keyboard():

    builder = InlineKeyboardBuilder()


    builder.row(
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="main_menu",
        )
    )


    return builder.as_markup()