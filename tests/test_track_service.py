from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.track import TrackService


@pytest.fixture
def service():
    service = TrackService.__new__(TrackService)
    service.repository = MagicMock()
    return service


# =====================================================
# _normalize_airport
# =====================================================

def test_normalize_airport_dict_with_code(service):
    result = service._normalize_airport(
        {
            "code": "mow",
            "city": "Москва",
        }
    )

    assert result == "MOW"


def test_normalize_airport_dict_without_code(service):
    result = service._normalize_airport(
        {
            "city": "Москва",
        }
    )

    assert result == "Москва"


def test_normalize_airport_string(service):
    assert service._normalize_airport(" led ") == "led"


def test_normalize_airport_none(service):
    assert service._normalize_airport(None) == ""


# =====================================================
# create_track
# =====================================================

@pytest.mark.asyncio
async def test_create_track_success(service):

    service.repository.exists = AsyncMock(
        return_value=False
    )

    created_track = object()

    service.repository.create = AsyncMock(
        return_value=created_track
    )

    result = await service.create_track(
        user_id=1,
        origin="MOW",
        destination="LED",
        departure_date=date(2026, 10, 10),
        target_price=10000,
    )

    assert result is created_track

    service.repository.exists.assert_awaited_once()

    service.repository.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_track_duplicate(service):

    service.repository.exists = AsyncMock(
        return_value=True
    )

    service.repository.create = AsyncMock()

    result = await service.create_track(
        user_id=1,
        origin="MOW",
        destination="LED",
        departure_date=date(2026, 10, 10),
    )

    assert result is None

    service.repository.create.assert_not_called()


# =====================================================
# delete_track
# =====================================================

@pytest.mark.asyncio
async def test_delete_track_success(service):

    track = object()

    service.repository.get_user_track = AsyncMock(
        return_value=track
    )

    service.repository.delete = AsyncMock()

    result = await service.delete_track(
        track_id=10,
        telegram_id=123,
    )

    assert result is True

    service.repository.delete.assert_awaited_once_with(
        track
    )


@pytest.mark.asyncio
async def test_delete_track_not_found(service):

    service.repository.get_user_track = AsyncMock(
        return_value=None
    )

    service.repository.delete = AsyncMock()

    result = await service.delete_track(
        track_id=10,
        telegram_id=123,
    )

    assert result is False

    service.repository.delete.assert_not_called()


# =====================================================
# update_target_price
# =====================================================

@pytest.mark.asyncio
async def test_update_target_price_success(service):

    track = object()

    updated = object()

    service.repository.get_by_id = AsyncMock(
        return_value=track
    )

    service.repository.update_target_price = AsyncMock(
        return_value=updated
    )

    result = await service.update_target_price(
        track_id=1,
        target_price=15000,
    )

    assert result is updated

    service.repository.update_target_price.assert_awaited_once_with(
        track,
        15000,
    )


@pytest.mark.asyncio
async def test_update_target_price_not_found(service):

    service.repository.get_by_id = AsyncMock(
        return_value=None
    )

    service.repository.update_target_price = AsyncMock()

    result = await service.update_target_price(
        track_id=1,
        target_price=15000,
    )

    assert result is None

    service.repository.update_target_price.assert_not_called()