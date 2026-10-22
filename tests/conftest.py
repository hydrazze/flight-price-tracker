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