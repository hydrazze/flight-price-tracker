from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database.base import Base
from app.handlers.my_tracks import show_price_history
from app.models import Track, User
from app.models.enums import StopPreference, TrackStatus
from app.models.price_history import PriceHistory
from app.repositories.track import TrackRepository
from app.repositories.price_history import PriceHistoryRepository
from app.schemas.travelpayouts import FlightPrice
from app.services.price_checker import PriceCheckerService
from app.services.notification import NotificationService
from app.utils.flight_formatter import format_flight_offer
from app.utils.timezone import format_moscow_time
from app.utils.track_formatter import format_track


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as value:
        yield value
    await engine.dispose()


async def seed_track(session, **overrides):
    user = User(telegram_id=123, first_name="Test")
    session.add(user)
    await session.flush()
    values = dict(
        user_id=user.id, user=user, origin="MOW", destination="BEG",
        departure_date=date(2027, 3, 10), stop_preference=StopPreference.ANY,
        no_flights_notified=False, target_price=None,
    )
    values.update(overrides)
    track = Track(**values)
    session.add(track)
    await session.commit()
    return track


def checker(session, flights, notifications=None):
    return PriceCheckerService(
        TrackRepository(session),
        SimpleNamespace(get_prices_for_dates=AsyncMock(return_value=SimpleNamespace(data=flights))),
        notifications or MagicMock(send_price_alert=AsyncMock(), send_no_flights_alert=AsyncMock()),
        PriceHistoryRepository(session),
    )


@pytest.mark.asyncio
async def test_cheapest_offer_and_price_survive_database_reload(session, flight_factory):
    track = await seed_track(session)
    best = flight_factory(price=12000, airline="JU", flight_number="650")
    other = flight_factory(price=20000, airline="SU", flight_number="100")
    service = checker(session, [other, best])
    await service.check_one_track(track.id)
    track_id = track.id
    session.expunge_all()
    stored = await TrackRepository(session).get_by_id(track_id)
    assert stored.last_price == 12000
    assert FlightPrice.model_validate(stored.last_offer) == best
    card = format_track(stored)
    assert "Air Serbia (JU)" in card
    assert "JU 650" in card
    assert "МСК" in card
    assert service.notification_service.send_price_alert.await_args.kwargs['offer'] == stored.last_offer


@pytest.mark.asyncio
async def test_offer_updates_without_price_change_or_extra_notification(session, flight_factory):
    previous = flight_factory(price=18000, airline="SU", flight_number="100")
    track = await seed_track(session, last_price=18000, last_offer=previous.model_dump(mode="json"))
    current = flight_factory(price=18000, airline="JU", flight_number="650", transfers=1)
    service = checker(session, [current])
    await service.check_one_track(track.id)
    assert track.last_offer['airline'] == 'JU'
    assert track.last_offer['transfers'] == 1
    service.notification_service.send_price_alert.assert_not_awaited()
    assert (await session.execute(select(PriceHistory))).scalars().all() == []


@pytest.mark.asyncio
async def test_no_flights_clears_offer_and_labels_previous_price(session, flight_factory):
    previous = flight_factory()
    track = await seed_track(session, last_price=previous.price, last_offer=previous.model_dump(mode="json"))
    await checker(session, []).check_one_track(track.id)
    assert track.last_offer is None
    assert track.last_price == previous.price
    card = format_track(track)
    assert "Последняя найденная цена" in card
    assert "Найденное предложение" not in card
    assert "Текущая цена" not in card


@pytest.mark.asyncio
async def test_failed_request_retains_offer_with_explicit_stale_label(session, flight_factory):
    previous = flight_factory()
    track = await seed_track(session, last_price=previous.price, last_offer=previous.model_dump(mode="json"))
    service = checker(session, [])
    service.client.get_prices_for_dates.side_effect = RuntimeError("provider unavailable")
    await service.check_one_track(track.id)
    assert track.status == TrackStatus.ERROR
    assert track.last_offer['airline'] == previous.airline
    assert "проверка не удалась" in format_track(track)
    assert "Последняя найденная цена" in format_track(track)


@pytest.mark.asyncio
async def test_notification_failure_preserves_price_offer_pair_and_retries(session, flight_factory):
    previous = flight_factory(price=20000)
    track = await seed_track(session, last_price=20000, last_offer=previous.model_dump(mode="json"))
    notifications = MagicMock(send_price_alert=AsyncMock(side_effect=[RuntimeError("telegram unavailable"), None]))
    service = checker(session, [flight_factory(price=12000)], notifications)
    await service.check_one_track(track.id)
    assert track.status == TrackStatus.ERROR
    assert track.last_offer['price'] == track.last_price == 20000
    await service.check_one_track(track.id)
    assert track.status == TrackStatus.AVAILABLE
    assert track.last_offer['price'] == track.last_price == 12000
    assert notifications.send_price_alert.await_count == 2


@pytest.mark.asyncio
async def test_history_times_are_moscow_time(session):
    track = await seed_track(session)
    session.add(PriceHistory(track_id=track.id, price=10000,
                             checked_at=datetime(2026, 10, 23, 19, 18, tzinfo=timezone.utc)))
    await session.commit()
    callback = MagicMock(data=f"price_history:{track.id}", answer=AsyncMock())
    callback.from_user.id = 123
    callback.message.edit_text = AsyncMock()
    await show_price_history(callback, session)
    assert "23.10.2026 22:18 МСК" in callback.message.edit_text.await_args.args[0]


@pytest.mark.parametrize("value,expected", [
    (datetime(2026,10,23,19,18,tzinfo=timezone.utc), "23.10.2026 22:18 МСК"),
    (datetime(2026,10,23,22,30,tzinfo=timezone.utc), "24.10.2026 01:30 МСК"),
    (datetime(2026,10,23,19,18), "23.10.2026 22:18 МСК"),
    (datetime(2026,10,23,20,18,tzinfo=timezone(timedelta(hours=1))), "23.10.2026 22:18 МСК"),
])
def test_moscow_time_handles_offsets_naive_utc_and_midnight(value, expected):
    assert format_moscow_time(value) == expected


def test_round_trip_offer_distinguishes_legs_and_missing_connection_airports(flight_factory):
    offer = flight_factory(transfers=1, return_transfers=2, return_at="2027-03-18T13:00:00+01:00")
    text = format_flight_offer(offer.model_dump(mode="json"))
    assert "Авиакомпания (туда): Air Serbia (JU)" in text
    assert "Туда: 1 пересадка" in text
    assert "Обратно: 2 пересадки" in text
    assert "Аэропорты пересадок: нет данных" in text
    assert "18.03.2027 13:00 (местное время)" in text
    assert 'href="https://www.aviasales.ru/search/' in text
    assert "&amp;price=" in text


def test_direct_flight_does_not_claim_connection(flight_factory):
    text = format_flight_offer(flight_factory().model_dump(mode="json"))
    assert "Туда: без пересадок" in text
    assert "Аэропорты пересадок" not in text
    assert "Обратно:" not in text


def test_unknown_inbound_stops_are_not_shown_as_direct(flight_factory):
    offer = flight_factory(return_at="2027-03-18T13:00:00+01:00", return_transfers=None)
    assert "Обратно: нет данных" in format_flight_offer(offer.model_dump(mode="json"))


@pytest.mark.parametrize("link", ["javascript:alert(1)", "https://evil.test/search/x", "//evil.test/search/x", "https://[broken"])
def test_external_or_malformed_offer_links_are_not_rendered(flight_factory, link):
    offer = flight_factory(link=link, airline="<XX>", flight_number="<b>injected</b>")
    text = format_flight_offer(offer.model_dump(mode="json"))
    assert 'href=' not in text
    assert '<b>injected</b>' not in text
    assert '&lt;XX&gt;' in text


def test_legacy_offerless_track_has_safe_upgrade_message():
    track = Track(origin="MOW", destination="BEG", departure_date=date(2027,3,10),
                  status=TrackStatus.AVAILABLE, last_price=18000)
    assert "после следующей успешной проверки" in format_track(track)
