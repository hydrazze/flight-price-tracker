from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.user import UserService


@pytest.fixture
def service():
    service = UserService.__new__(UserService)
    service.repository = MagicMock()
    return service


@pytest.mark.asyncio
async def test_get_existing_user(service):

    user = object()

    service.repository.get_by_telegram_id = AsyncMock(
        return_value=user
    )

    result = await service.get_or_create(
        telegram_id=1,
        username="hydraze",
        first_name="Hydra",
        last_name=None,
    )

    assert result is user

    service.repository.create.assert_not_called()


@pytest.mark.asyncio
async def test_create_new_user(service):

    created = object()

    service.repository.get_by_telegram_id = AsyncMock(
        return_value=None
    )

    service.repository.create = AsyncMock(
        return_value=created
    )

    result = await service.get_or_create(
        telegram_id=1,
        username="hydraze",
        first_name="Hydra",
        last_name=None,
    )

    assert result is created

    service.repository.create.assert_awaited_once_with(
        telegram_id=1,
        username="hydraze",
        first_name="Hydra",
        last_name=None,
    )


@pytest.mark.asyncio
async def test_get_by_telegram_id(service):

    user = object()

    service.repository.get_by_telegram_id = AsyncMock(
        return_value=user
    )

    result = await service.get_by_telegram_id(
        12345
    )

    assert result is user

    service.repository.get_by_telegram_id.assert_awaited_once_with(
        12345
    )