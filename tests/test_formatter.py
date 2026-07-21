from datetime import date, datetime, timezone

from app.models import Track
from app.models.enums import TrackStatus
from app.utils.track_formatter import (
    format_route,
    get_track_status,
    format_track,
    format_tracks_list,
    format_archive_track,
)


def create_track(
    status=TrackStatus.UNKNOWN,
    target_price=10000,
    last_price=8000,
):
    return Track(
        id=1,
        user_id=1,
        origin="MOW",
        destination="LED",
        departure_date=date(2026, 8, 10),
        target_price=target_price,
        last_price=last_price,
        status=status,
        last_checked_at=datetime(
            2026,
            7,
            20,
            12,
            30,
            tzinfo=timezone.utc,
        ),
        active=True,
        no_flights_notified=False,
    )


def test_format_route():

    result = format_route(
        "MOW",
        "LED",
    )

    assert "MOW" in result
    assert "LED" in result
    assert "→" in result



def test_status_available():

    track = create_track(
        status=TrackStatus.AVAILABLE
    )

    assert get_track_status(track) == "✅ Рейсы найдены"



def test_status_not_found():

    track = create_track(
        status=TrackStatus.NOT_FOUND
    )

    assert get_track_status(track) == "❌ Рейсы не найдены"



def test_status_error():

    track = create_track(
        status=TrackStatus.ERROR
    )

    assert get_track_status(track) == "⚠️ Ошибка проверки"



def test_status_archived():

    track = create_track(
        status=TrackStatus.ARCHIVED
    )

    assert get_track_status(track) == "🗂 Архив"



def test_status_unknown():

    track = create_track(
        status=TrackStatus.UNKNOWN
    )

    assert get_track_status(track) == "⏳ Ожидает проверки"



def test_format_track_contains_data():

    track = create_track()

    result = format_track(track)

    assert "Дата вылета" in result
    assert "10.08.2026" in result
    assert "10000" in result
    assert "8000" in result
    assert "Последняя проверка" in result



def test_format_track_without_prices():

    track = create_track(
        target_price=None,
        last_price=None,
    )

    result = format_track(track)

    assert "не указана" in result
    assert "нет данных" in result



def test_format_tracks_list_empty():

    result = format_tracks_list([])

    assert "Пока нет активных треков" in result



def test_format_tracks_list():

    track = create_track()

    result = format_tracks_list(
        [track]
    )

    assert "MOW" in result
    assert "LED" in result
    assert "10000" in result



def test_archive_format():

    track = create_track()

    result = format_archive_track(track)

    assert "Рейс состоялся" in result
    assert "10.08.2026" in result