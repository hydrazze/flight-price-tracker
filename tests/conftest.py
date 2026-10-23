import os

# Always isolate tests from any developer's API credentials and database.
os.environ["BOT_TOKEN"] = "123456789:AA123456789012345678901234567890123"
os.environ["TRAVELPAYOUTS_API_KEY"] = "test_api_key"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

import pytest


@pytest.fixture
def sample_track_data():
    return {
        "origin": "MOW",
        "destination": "LED",
        "target_price": 10000,
    }

@pytest.fixture
def flight_factory():
    from app.schemas.travelpayouts import FlightPrice

    def make(**changes):
        data = {
            "origin": "MOW", "destination": "BEG", "origin_airport": "SVO",
            "destination_airport": "BEG", "price": 18000,
            "airline": "JU", "flight_number": "651",
            "departure_at": "2027-03-10T10:00:00+03:00",
            "return_at": None, "transfers": 0, "return_transfers": None,
            "duration": 180, "duration_to": 180,
            "link": "/search/MOW1003BEG1?t=test&price=18000",
        }
        data.update(changes)
        return FlightPrice.model_validate(data)

    return make
