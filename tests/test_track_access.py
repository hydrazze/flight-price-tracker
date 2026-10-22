from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database.base import Base
from app.models import User, Track
from app.repositories.track import TrackRepository
from app.services.track import TrackService
from app.services.price_checker import PriceCheckerService
from app.handlers import my_tracks


@pytest_asyncio.fixture
async def tracks():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        owner = User(telegram_id=100, first_name="Owner")
        stranger = User(telegram_id=200, first_name="Stranger")
        session.add_all([owner, stranger])
        await session.flush()
        own = Track(user_id=owner.id, origin="MOW", destination="LED",
                    departure_date=date.today() + timedelta(days=7))
        other = Track(user_id=stranger.id, origin="LED", destination="MOW",
                      departure_date=date.today() + timedelta(days=7))
        session.add_all([own, other])
        await session.commit()
        own_id, other_id = own.id, other.id
    # Fresh session is essential to exercise async relationship loading.
    async with sessions() as session:
        yield session, own_id, other_id
    await engine.dispose()


@pytest.mark.asyncio
async def test_only_owner_can_update_or_delete_track(tracks):
    session, own_id, other_id = tracks
    service = TrackService(session)
    assert await service.update_target_price(other_id, 1000, telegram_id=100) is None
    assert await service.delete_track(other_id, telegram_id=100) is False
    updated = await service.update_target_price(own_id, 2000, telegram_id=100)
    assert updated.target_price == 2000
    assert (await TrackRepository(session).get_by_id(other_id)).target_price is None


@pytest.mark.asyncio
@pytest.mark.parametrize("handler,prefix", [
    (my_tracks.open_track, "track"),
    (my_tracks.show_price_history, "price_history"),
    (my_tracks.edit_target_price, "edit_target_price"),
    (my_tracks.delete_track_confirm, "delete_track"),
    (my_tracks.check_track_now, "check_track"),
])
async def test_foreign_callbacks_are_rejected(tracks, handler, prefix):
    session, _, other_id = tracks
    callback = MagicMock()
    callback.data = f"{prefix}:{other_id}"
    callback.from_user.id = 100
    callback.answer = AsyncMock()
    callback.message.edit_text = AsyncMock()
    state = AsyncMock()
    args = {"callback": callback, "session": session}
    if handler is my_tracks.edit_target_price:
        args["state"] = state
    await handler(**args)
    callback.answer.assert_awaited_once_with(
        "❌ Отслеживание не найдено.", show_alert=True
    )
    callback.message.edit_text.assert_not_awaited()
    state.set_state.assert_not_awaited()


@pytest.mark.asyncio
async def test_manual_check_reads_user_and_notifies_with_fresh_session(tracks):
    session, own_id, _ = tracks
    repository = TrackRepository(session)
    client = MagicMock(get_prices_for_dates=AsyncMock(return_value=MagicMock(data=[])))
    notifications = MagicMock(send_no_flights_alert=AsyncMock())
    service = PriceCheckerService(repository, client, notifications, MagicMock())
    await service.check_one_track(own_id)
    assert notifications.send_no_flights_alert.await_args.kwargs["telegram_id"] == 100
    client.get_prices_for_dates.assert_awaited_once()


@pytest.mark.asyncio
async def test_user_check_does_not_archive_or_query_other_users(tracks):
    session, own_id, other_id = tracks
    repository = TrackRepository(session)
    own = await repository.get_by_id(own_id)
    other = await repository.get_by_id(other_id)
    own.departure_date = other.departure_date = date.today() - timedelta(days=1)
    await session.commit()
    notifications = MagicMock(send_track_expired_alert=AsyncMock())
    client = MagicMock(get_prices_for_dates=AsyncMock())
    service = PriceCheckerService(repository, client, notifications, MagicMock())
    await service.check_prices(telegram_id=100)
    assert own.active is False
    assert other.active is True
    notifications.send_track_expired_alert.assert_awaited_once()
    client.get_prices_for_dates.assert_not_awaited()


@pytest.mark.asyncio
async def test_manual_user_check_only_requests_own_route(tracks):
    session, _, _ = tracks
    client = MagicMock(get_prices_for_dates=AsyncMock(return_value=MagicMock(data=[])))
    notifications = MagicMock(send_no_flights_alert=AsyncMock())
    service = PriceCheckerService(TrackRepository(session), client, notifications, MagicMock())
    await service.check_prices(telegram_id=100)
    client.get_prices_for_dates.assert_awaited_once()
    assert client.get_prices_for_dates.await_args.kwargs["origin"] == "MOW"
    assert notifications.send_no_flights_alert.await_args.kwargs["telegram_id"] == 100


@pytest.mark.asyncio
async def test_callback_dispatch_gets_database_session(tracks, monkeypatch):
    """Exercise aiogram routing and middleware, not just a direct handler call."""
    from contextlib import asynccontextmanager
    from aiogram.types import Update
    from app.bot import bot, dispatcher
    from app.handlers import router
    from app.middlewares import database

    session, _, other_id = tracks

    @asynccontextmanager
    async def session_context():
        yield session

    monkeypatch.setattr(database, "async_session_maker", session_context)
    request = AsyncMock(return_value=True)
    monkeypatch.setattr(bot.session, "make_request", request)
    dispatcher.include_router(router)
    update = Update.model_validate({
        "update_id": 1,
        "callback_query": {
            "id": "test-callback", "chat_instance": "test-chat",
            "from": {"id": 100, "is_bot": False, "first_name": "Owner"},
            "data": f"track:{other_id}",
            "message": {
                "message_id": 1, "date": 0,
                "chat": {"id": 100, "type": "private"}, "text": "Tracks",
            },
        },
    })
    await dispatcher.feed_update(bot, update)
    request.assert_awaited_once()
    method = request.await_args.args[1]
    assert method.__api_method__ == "answerCallbackQuery"
    assert method.show_alert is True
