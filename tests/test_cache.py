from datetime import date
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from redis.exceptions import ConnectionError, TimeoutError

from app.cache.redis import RedisCache
from app.providers import travelpayouts


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [ConnectionError, TimeoutError])
async def test_unavailable_redis_does_not_block_cache_operations(failure):
    cache = RedisCache.__new__(RedisCache)
    cache.redis = MagicMock(
        get=AsyncMock(side_effect=failure),
        set=AsyncMock(side_effect=failure),
        delete=AsyncMock(side_effect=failure),
    )
    assert await cache.get("key") is None
    await cache.set("key", "value")
    await cache.delete("key")


@pytest.mark.asyncio
@pytest.mark.parametrize("cached", ["broken-json", '{"wrong": "schema"}'])
async def test_corrupt_cache_fetches_and_stores_valid_api_response(monkeypatch, cached):
    cache = MagicMock(get=AsyncMock(return_value=cached), delete=AsyncMock(), set=AsyncMock())
    monkeypatch.setattr(travelpayouts, "redis_cache", cache)
    client = travelpayouts.TravelPayoutsClient()
    await client.client.aclose()
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json={"success": True, "data": [], "currency": "rub"})

    client.client = httpx.AsyncClient(base_url=client.BASE_URL, transport=httpx.MockTransport(respond))
    try:
        result = await client.get_prices_for_dates("MOW", "LED", date(2027, 1, 1))
        assert result.data == []
        assert len(requests) == 1
        cache.delete.assert_awaited_once()
        cache.set.assert_awaited_once()
    finally:
        await client.close()
