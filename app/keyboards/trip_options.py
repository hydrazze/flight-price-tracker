from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.models.enums import StopPreference


trip_type_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="➡️ В одну сторону", callback_data="trip:one_way")],
    [InlineKeyboardButton(text="↔️ Туда и обратно", callback_data="trip:round_trip")],
    [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_track")],
])

stop_preference_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=preference.label, callback_data=f"stops:{preference.value}")]
    for preference in StopPreference
] + [[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_track")]])
