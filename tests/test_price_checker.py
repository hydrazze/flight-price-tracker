import pytest
from types import SimpleNamespace
from datetime import date
from unittest.mock import AsyncMock, MagicMock
from app.models.enums import StopPreference, TrackStatus

from app.services.price_checker import PriceCheckerService


def checker():
    return PriceCheckerService(
        repository=None,
        client=None,
        notification_service=None,
        price_history_repository=None,
    )


def test_should_notify_first_price_without_target():
    service = checker()

    assert service.should_notify(
        old_price=None,
        new_price=10000,
        target_price=None,
    ) is True


def test_should_notify_price_changed():
    service = checker()

    assert service.should_notify(
        old_price=12000,
        new_price=11000,
        target_price=None,
    ) is True


def test_should_not_notify_same_price():
    service = checker()

    assert service.should_notify(
        old_price=12000,
        new_price=12000,
        target_price=None,
    ) is False


def test_should_notify_when_target_reached():
    service = checker()

    assert service.should_notify(
        old_price=12000,
        new_price=9000,
        target_price=10000,
    ) is True


def test_should_not_notify_when_target_not_reached():
    service = checker()

    assert service.should_notify(
        old_price=12000,
        new_price=11000,
        target_price=10000,
    ) is False


def test_should_notify_first_price_if_target_already_reached():
    service = checker()

    assert service.should_notify(
        old_price=None,
        new_price=9000,
        target_price=10000,
    ) is True


def test_should_not_notify_first_price_if_target_not_reached():
    service = checker()

    assert service.should_notify(
        old_price=None,
        new_price=12000,
        target_price=10000,
    ) is False

# A fresh no-flights episode should notify again after flights reappear.


@pytest.mark.asyncio
async def test_no_flights_notification_resets_when_flights_reappear(flight_factory):
    track = SimpleNamespace(
        id=1, origin="MOW", destination="LED", departure_date=date(2027, 1, 1),
        user=SimpleNamespace(telegram_id=123), no_flights_notified=True,
        last_price=10000, target_price=None,
        return_date=None, stop_preference=StopPreference.ANY,
    )
    client = MagicMock(get_prices_for_dates=AsyncMock(side_effect=[
        SimpleNamespace(data=[flight_factory(price=10000)]),
        SimpleNamespace(data=[]),
        SimpleNamespace(data=[]),
    ]))
    notifications = MagicMock(send_no_flights_alert=AsyncMock())
    service = PriceCheckerService(None, client, notifications, MagicMock())
    await service._check_track(track)
    assert track.status == TrackStatus.AVAILABLE
    assert track.no_flights_notified is False
    await service._check_track(track)
    await service._check_track(track)
    assert track.status == TrackStatus.NOT_FOUND
    notifications.send_no_flights_alert.assert_awaited_once()
