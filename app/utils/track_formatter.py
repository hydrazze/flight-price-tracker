from app.models.track import Track
from app.services.city_resolver import resolver


def format_route(origin: str, destination: str) -> str:
    origin_name = resolver.get_city_name(origin)
    destination_name = resolver.get_city_name(destination)

    return f"{origin_name} ({origin.upper()}) → {destination_name} ({destination.upper()})"



def get_track_status(
    track: Track,
) -> str:

    if track.status.value == "available":
        return "✅ Рейсы найдены"

    elif track.status.value == "not_found":
        return "❌ Рейсы не найдены"

    elif track.status.value == "error":
        return "⚠️ Ошибка проверки"

    return "⏳ Ожидает проверки"



def format_track(
    track: Track,
) -> str:

    last_checked = (
        track.last_checked_at.strftime(
            "%d.%m.%Y %H:%M"
        )
        if track.last_checked_at
        else "нет данных"
    )


    return (
        f"✈️ Маршрут:\n"
        f"{format_route(track.origin, track.destination)}\n\n"

        f"📅 Дата вылета:\n"
        f"{track.departure_date.strftime('%d.%m.%Y')}\n\n"

        f"🎯 Целевая цена:\n"
        f"{track.target_price if track.target_price is not None else 'не указана'} ₽\n\n"

        f"📉 Текущая цена:\n"
        f"{track.last_price if track.last_price is not None else 'нет данных'} ₽\n\n"

        f"{get_track_status(track)}\n"
        f"🕒 Последняя проверка: {last_checked}"
    )



def format_tracks_list(
    tracks: list[Track],
) -> str:

    text = "📋 Ваши отслеживания:\n\n"


    for track in tracks:

        text += (
            f"✈️ {format_route(track.origin, track.destination)}\n"
            f"📅 {track.departure_date.strftime('%d.%m.%Y')}\n"
            f"💰 "
            f"{track.last_price if track.last_price else 'нет данных'} ₽\n\n"
        )


    return text



def format_archive_track(
    track: Track,
) -> str:

    return (
        f"✈️ {format_route(track.origin, track.destination)}\n"
        f"📅 Дата вылета: "
        f"{track.departure_date.strftime('%d.%m.%Y')}\n"
        f"🛫 Рейс состоялся\n"
    )