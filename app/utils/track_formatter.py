from app.models.track import Track


def get_track_status(track: Track) -> str:

    if track.status.value == "available":
        return "✅ Рейсы найдены"

    elif track.status.value == "not_found":
        return "❌ Рейсы не найдены"

    elif track.status.value == "error":
        return "⚠️ Ошибка проверки"

    return "⏳ Ожидает проверки"



def format_track(track: Track) -> str:

    last_checked = (
        track.last_checked_at.strftime(
            "%d.%m.%Y %H:%M"
        )
        if track.last_checked_at
        else "нет данных"
    )


    return (
        f"✈️ {track.origin} → {track.destination}\n\n"
        f"📅 Дата: {track.departure_date.strftime('%d-%m-%Y')}\n"
        f"🎯 Цель: "
        f"{track.target_price if track.target_price is not None else 'не указана'} ₽\n"
        f"📉 Сейчас: "
        f"{track.last_price if track.last_price is not None else 'нет данных'} ₽\n"
        f"{get_track_status(track)}\n"
        f"🕒 Проверено: {last_checked}"
    )



def format_tracks_list(
    tracks: list[Track],
) -> str:

    text = "Ваши отслеживания:\n\n"


    for track in tracks:

        text += (
            f"✈️ {track.origin} → {track.destination}\n"
            f"📅 {track.departure_date.strftime('%d-%m-%Y')}\n"
            f"🎯 Цель: "
            f"{track.target_price if track.target_price is not None else 'не указана'} ₽\n"
            f"📉 Сейчас: "
            f"{track.last_price if track.last_price is not None else 'нет данных'} ₽\n\n"
        )


    return text

def format_archive_track(track):

    return (
        f"✈️ {track.origin} → {track.destination}\n"
        f"📅 Дата вылета: "
        f"{track.departure_date.strftime('%d-%m-%Y')}\n"
        f"🛫 Рейс состоялся\n"
    )