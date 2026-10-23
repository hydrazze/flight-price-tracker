from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database.base import Base
from app.handlers import track as handlers
from app.models import Track, User
from app.models.enums import StopPreference, TrackStatus
from app.services.track import TrackService
from app.services.price_checker import PriceCheckerService
from app.services.notification import NotificationService
from app.states.track import TrackState
from app.utils.track_formatter import format_track, format_tracks_list, format_archive_track
from app.keyboards.tracks import tracks_keyboard


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as value:
        yield value
    await engine.dispose()


def message(text=None):
    result = MagicMock(text=text)
    result.from_user.id = 123
    result.from_user.username = "test"
    result.from_user.first_name = "Test"
    result.from_user.last_name = None
    result.answer = AsyncMock()
    result.edit_reply_markup = AsyncMock()
    return result


def callback(data, msg):
    return MagicMock(data=data, message=msg, answer=AsyncMock())


@pytest.mark.asyncio
@pytest.mark.parametrize("round_trip", [False, True])
@pytest.mark.parametrize("preference", list(StopPreference))
async def test_create_dialog_persists_every_trip_option(session, round_trip, preference):
    storage = MemoryStorage()
    state = FSMContext(storage=storage, key=StorageKey(bot_id=1, chat_id=123, user_id=123))
    outbound = date.today() + timedelta(days=7)
    inbound = outbound + timedelta(days=7)
    await handlers.start_track_creation(message(), state)
    await handlers.process_origin(message("MOW"), state)
    await handlers.process_destination(message("LED"), state)
    await handlers.process_date(message(outbound.isoformat()), state)
    assert await state.get_state() == TrackState.waiting_trip_type.state
    trip = "round_trip" if round_trip else "one_way"
    await handlers.process_trip_type(callback(f"trip:{trip}", message()), state)
    if round_trip:
        assert await state.get_state() == TrackState.waiting_return_date.state
        await handlers.process_return_date(message(inbound.isoformat()), state)
    assert await state.get_state() == TrackState.waiting_stop_preference.state
    await handlers.process_stop_preference(callback(f"stops:{preference.value}", message()), state)
    assert await state.get_state() == TrackState.waiting_target_price.state
    confirmation = message("20000")
    await handlers.process_target_price(confirmation, state, session)
    stored = (await session.execute(select(Track))).scalar_one()
    assert stored.return_date == (inbound if round_trip else None)
    assert stored.stop_preference == preference
    assert stored.target_price == 20000
    assert await state.get_state() is None
    assert preference.label in confirmation.answer.await_args.args[0]
    if round_trip:
        assert inbound.strftime("%d.%m.%Y") in confirmation.answer.await_args.args[0]
    await storage.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("text", [None, "wrong", "2000-01-01"])
async def test_invalid_return_date_keeps_dialog_at_return_step(text):
    state = AsyncMock()
    state.get_data.return_value = {"departure_date": date(2027, 1, 10)}
    msg = message(text)
    await handlers.process_return_date(msg, state)
    state.update_data.assert_not_awaited()
    state.set_state.assert_not_awaited()
    msg.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_duplicate_detection_includes_return_date_and_preferences(session):
    session.add(User(id=1, telegram_id=123, first_name="Test"))
    await session.commit()
    service = TrackService(session)
    outbound = date(2027, 1, 10)
    inbound = date(2027, 1, 20)
    options = [(None, StopPreference.ANY), (None, StopPreference.DIRECT),
               (inbound, StopPreference.ANY), (inbound, StopPreference.WITH_STOPS),
               (inbound + timedelta(days=1), StopPreference.ANY)]
    for back, preference in options:
        kwargs = dict(user_id=1, origin="MOW", destination="LED", departure_date=outbound,
                      return_date=back, stop_preference=preference)
        stored = await service.create_track(**kwargs)
        assert stored is not None
        assert await service.create_track(**kwargs) is None
    with pytest.raises(ValueError):
        await service.create_track(1, "MOW", "LED", inbound, return_date=outbound)


@pytest.mark.asyncio
async def test_checker_passes_round_trip_options_and_uses_total_price(flight_factory):
    from types import SimpleNamespace
    track = Track(id=1, user_id=1, origin="MOW", destination="LED",
                  departure_date=date(2027, 1, 10), return_date=date(2027, 1, 20),
                  stop_preference=StopPreference.WITH_STOPS, last_price=None,
                  target_price=10000, no_flights_notified=False)
    track.user = User(telegram_id=123, first_name="Test")
    client = MagicMock(get_prices_for_dates=AsyncMock(return_value=SimpleNamespace(
        data=[flight_factory(price=9000), flight_factory(price=12000)])))
    notices = MagicMock(send_price_alert=AsyncMock())
    history = MagicMock(create=AsyncMock())
    checker = PriceCheckerService(None, client, notices, history)
    await checker._check_track(track)
    assert track.status == TrackStatus.AVAILABLE
    assert track.last_price == 9000
    assert client.get_prices_for_dates.await_args.kwargs['return_date'] == track.return_date
    assert client.get_prices_for_dates.await_args.kwargs['stop_preference'] == StopPreference.WITH_STOPS
    assert notices.send_price_alert.await_args.kwargs['new_price'] == 9000
    assert notices.send_price_alert.await_args.kwargs['return_date'] == track.return_date
    history.create.assert_awaited_once_with(track_id=1, price=9000)


@pytest.mark.asyncio
async def test_round_trip_is_visible_in_cards_archive_buttons_and_alerts():
    track = Track(id=1, origin="MOW", destination="LED", departure_date=date(2027, 1, 10),
                  return_date=date(2027, 1, 20), stop_preference=StopPreference.DIRECT,
                  status=TrackStatus.AVAILABLE, last_price=15000)
    for formatted in [format_track(track), format_tracks_list([track]), format_archive_track(track)]:
        assert '20.01.2027' in formatted
        assert 'Без пересадок' in formatted
        assert '↔' in formatted
    assert '20.01.27' in tracks_keyboard([track]).inline_keyboard[0][0].text
    bot = MagicMock(send_message=AsyncMock())
    await NotificationService(bot).send_price_alert(
        123, 'MOW', 'LED', track.departure_date, None, 15000, None,
        return_date=track.return_date, stop_preference=track.stop_preference,
    )
    text = bot.send_message.await_args.kwargs['text']
    assert '20.01.2027' in text
    assert 'всю поездку' in text
    assert 'Без пересадок' in text


@pytest.mark.asyncio
async def test_return_on_departure_day_is_supported(session):
    session.add(User(id=1, telegram_id=123, first_name="Test"))
    await session.commit()
    same_day = date(2027, 1, 10)
    track = await TrackService(session).create_track(
        1, "MOW", "LED", same_day, return_date=same_day,
    )
    assert track.return_date == track.departure_date
