from datetime import date
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
import pytest_asyncio

from app.models.enums import StopPreference
from app.providers import travelpayouts

DEPARTURE = date(2027, 1, 10)
RETURN = date(2027, 1, 20)


def flight(price, transfers=0, return_transfers=None, return_date=None, departure=DEPARTURE):
    return {
        "origin": "MOW", "destination": "LED", "origin_airport": "SVO",
        "destination_airport": "LED", "price": price, "airline": "SU",
        "flight_number": "100", "departure_at": f"{departure}T12:00:00+03:00",
        "return_at": f"{return_date}T12:00:00+03:00" if return_date else None,
        "transfers": transfers, "return_transfers": return_transfers,
        "duration": 180, "duration_to": 90, "duration_back": 90,
        "link": "/test",
    }


@pytest_asyncio.fixture
async def provider(monkeypatch):
    cache = MagicMock(get=AsyncMock(return_value=None), set=AsyncMock(), delete=AsyncMock())
    monkeypatch.setattr(travelpayouts, "redis_cache", cache)
    client = travelpayouts.TravelPayoutsClient()
    await client.client.aclose()
    requests = []
    pages = [[]]

    def respond(request):
        requests.append(request)
        page = int(request.url.params["page"])
        return httpx.Response(200, json={
            "success": True, "currency": "rub", "data": pages[page - 1],
        })

    client.client = httpx.AsyncClient(base_url=client.BASE_URL, transport=httpx.MockTransport(respond))
    yield client, cache, requests, pages
    await client.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("preference,expected", [
    (StopPreference.ANY, [1000, 2000]),
    (StopPreference.DIRECT, [1000]),
    (StopPreference.WITH_STOPS, [2000]),
])
async def test_one_way_options_and_exact_date_filter(provider, preference, expected):
    client, _, requests, pages = provider
    pages[0] = [flight(1000), flight(2000, transfers=1),
                flight(300, return_date=RETURN), flight(400, departure=RETURN)]
    result = await client.get_prices_for_dates("MOW", "LED", DEPARTURE, stop_preference=preference)
    assert [item.price for item in result.data] == expected
    params = requests[0].url.params
    assert params["one_way"] == "true"
    assert "return_at" not in params
    assert params["direct"] == ("true" if preference == StopPreference.DIRECT else "false")
    assert params["unique"] == "false"


@pytest.mark.asyncio
@pytest.mark.parametrize("preference,expected", [
    (StopPreference.ANY, [1000, 2000, 3000, 4000, 5000]),
    (StopPreference.DIRECT, [1000]),
    (StopPreference.WITH_STOPS, [2000, 3000, 4000]),
])
async def test_round_trip_filters_both_legs_and_return_date(provider, preference, expected):
    client, _, requests, pages = provider
    pages[0] = [
        flight(1000, return_date=RETURN, return_transfers=0),
        flight(2000, transfers=1, return_date=RETURN, return_transfers=0),
        flight(3000, return_date=RETURN, return_transfers=1),
        flight(4000, transfers=2, return_date=RETURN, return_transfers=1),
        flight(5000, return_date=RETURN),  # Unknown inbound stops must not mean direct.
        flight(100),  # One-way fare must not be compared to a round-trip target.
        flight(200, return_date=date(2027, 1, 21), return_transfers=0),
    ]
    result = await client.get_prices_for_dates("MOW", "LED", DEPARTURE, RETURN, preference)
    assert [item.price for item in result.data] == expected
    assert requests[0].url.params["one_way"] == "false"
    assert requests[0].url.params["return_at"] == RETURN.isoformat()


@pytest.mark.asyncio
async def test_connecting_fare_on_later_page_is_found(provider):
    client, _, requests, pages = provider
    client.PAGE_SIZE = 2
    pages[:] = [[flight(1000), flight(1100)], [flight(2000, transfers=1)]]
    price = await client.get_current_price("MOW", "LED", DEPARTURE, stop_preference=StopPreference.WITH_STOPS)
    assert price == 2000
    assert [r.url.params["page"] for r in requests] == ["1", "2"]


def test_cache_keys_separate_all_trip_options():
    client = travelpayouts.TravelPayoutsClient.__new__(travelpayouts.TravelPayoutsClient)
    keys = {
        client._cache_key("MOW", "LED", DEPARTURE, back, preference)
        for back in [None, RETURN, date(2027, 1, 21)]
        for preference in StopPreference
    }
    assert len(keys) == 9


@pytest.mark.asyncio
async def test_cached_result_avoids_api(provider):
    client, cache, requests, _ = provider
    cache.get.return_value = '{"success":true,"data":[],"currency":"rub"}'
    result = await client.get_prices_for_dates("MOW", "LED", DEPARTURE, RETURN, StopPreference.DIRECT)
    assert result.data == []
    assert requests == []
    cache.get.assert_awaited_once_with(client._cache_key("MOW", "LED", DEPARTURE, RETURN, StopPreference.DIRECT))


@pytest.mark.asyncio
async def test_bad_return_date_does_not_call_api_or_cache(provider):
    client, cache, requests, _ = provider
    with pytest.raises(ValueError):
        await client.get_prices_for_dates("MOW", "LED", RETURN, DEPARTURE)
    cache.get.assert_not_awaited()
    assert requests == []


@pytest.mark.asyncio
async def test_unsuccessful_api_response_is_not_cached_as_no_flights(provider):
    client, cache, _, _ = provider
    await client.client.aclose()
    client.client = httpx.AsyncClient(base_url=client.BASE_URL, transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json={"success": False, "data": [], "currency": "rub"})))
    with pytest.raises(RuntimeError, match="unsuccessful"):
        await client.get_prices_for_dates("MOW", "LED", DEPARTURE)
    cache.set.assert_not_awaited()


@pytest.mark.asyncio
async def test_repeated_full_api_page_does_not_loop_forever(provider):
    client, cache, requests, pages = provider
    client.PAGE_SIZE = 1
    pages[:] = [[flight(1000)], [flight(1000)]]
    with pytest.raises(RuntimeError, match="repeated a page"):
        await client.get_prices_for_dates("MOW", "LED", DEPARTURE)
    assert len(requests) == 2
    cache.set.assert_not_awaited()
