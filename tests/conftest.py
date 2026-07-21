import pytest


@pytest.fixture
def sample_track_data():
    return {
        "origin": "MOW",
        "destination": "LED",
        "target_price": 10000,
    }