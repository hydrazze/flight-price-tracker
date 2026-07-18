from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from app.models.track import Track



def tracks_keyboard(
    tracks: list[Track],
):

    builder = InlineKeyboardBuilder()


    for track in tracks:

        builder.button(
            text=f"✈️ {track.origin} → {track.destination}",
            callback_data=f"track:{track.id}",
        )


    builder.adjust(1)


    return builder.as_markup()



def track_detail_keyboard(track_id: int):

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="✏️ Изменить цену",
            callback_data=f"edit_target_price:{track_id}",
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

    return builder.as_markup()



def delete_confirm_keyboard(
    track_id: int,
):

    builder = InlineKeyboardBuilder()


    builder.button(
        text="✅ Да, удалить",
        callback_data=f"confirm_delete:{track_id}",
    )


    builder.button(
        text="⬅️ Отмена",
        callback_data=f"track:{track_id}",
    )


    builder.adjust(1)


    return builder.as_markup()