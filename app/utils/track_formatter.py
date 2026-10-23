from datetime import date

from app.models.track import Track
from app.models.enums import StopPreference
from app.services.city_resolver import resolver


def format_route(origin: str, destination: str) -> str:
    origin_name = resolver.get_city_name(origin)
    destination_name = resolver.get_city_name(destination)

    return f"{origin_name} ({str(origin).upper()}) → {destination_name} ({str(destination).upper()})"


def format_itinerary(
    origin: str,
    destination: str,
    departure_date: date,
    return_date: date | None = None,
    stop_preference: StopPreference = StopPreference.ANY,
) -> str:
    route = format_route(origin, destination)
    if return_date is not None:
        route = route.replace(" → ", " ↔ ")
    text = f"✈️ {route}\n📅 Дата вылета: {departure_date.strftime('%d.%m.%Y')}\n"
    if return_date is not None:
        text += f"📅 Обратно: {return_date.strftime('%d.%m.%Y')}\n"
    else:
        text += "➡️ В одну сторону\n"
    preference = StopPreference(stop_preference or StopPreference.ANY)
    return text + f"🛫 {preference.label}"


def format_track_itinerary(track: Track) -> str:
    return format_itinerary(
        track.origin, track.destination, track.departure_date,
        track.return_date, track.stop_preference,
    )


def get_track_status(track: Track) -> str:
    status_value = getattr(track.status, "value", track.status)

    if status_value == "available":
        return "✅ Рейсы найдены"

    if status_value == "not_found":
        return "❌ Рейсы не найдены"

    if status_value == "error":
        return "⚠️ Ошибка проверки"

    if status_value == "archived":
        return "🗂 Архив"

    return "⏳ Ожидает проверки"


def format_track(track: Track) -> str:
    last_checked = (
        track.last_checked_at.strftime("%d.%m.%Y %H:%M")
        if track.last_checked_at
        else "нет данных"
    )

    price_scope = "Цена за всю поездку туда и обратно.\n" if track.return_date else ""
    return (
        f"{format_track_itinerary(track)}\n\n"
        f"{price_scope}"
        f"🎯 Целевая цена:\n"
        f"{track.target_price if track.target_price is not None else 'не указана'} ₽\n\n"
        f"📉 Текущая цена:\n"
        f"{track.last_price if track.last_price is not None else 'нет данных'} ₽\n\n"
        f"{get_track_status(track)}\n"
        f"🕒 Последняя проверка: {last_checked}"
    )


def format_tracks_list(tracks: list[Track]) -> str:
    if not tracks:
        return "📋 Ваши отслеживания:\n\nПока нет активных треков."

    text = "📋 Ваши отслеживания:\n\n"

    for track in tracks:
        text += f"{format_track_itinerary(track)}\n"
        if track.return_date:
            text += "Цена за всю поездку туда и обратно.\n"

        if track.target_price is not None:
            text += f"🎯 Цель: {track.target_price} ₽\n"
        else:
            text += "🎯 Цель: не указана\n"

        if track.last_price is not None:
            text += f"💰 {track.last_price} ₽\n"

        text += f"{get_track_status(track)}\n\n"

    return text


def format_archive_track(track: Track) -> str:
    return (
        f"{format_track_itinerary(track)}\n"
        f"🛫 {'Отслеживание завершено' if track.return_date else 'Рейс состоялся'}\n"
    )
