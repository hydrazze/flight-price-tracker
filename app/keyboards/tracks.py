from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.models.track import Track


def tracks_keyboard(tracks: list[Track]):

    builder = InlineKeyboardBuilder()

    for track in tracks:
        builder.button(
            text=f"❌ {track.origin} → {track.destination}",
            callback_data=f"delete_track:{track.id}",
        )

    builder.adjust(1)

    return builder.as_markup()