from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from app.config.settings import Settings
from app.handlers.my_tracks import process_edit_target_price
from app.handlers.track import process_target_price
from app.utils.date_parser import parse_date


@pytest.mark.parametrize("interval", [0, -1])
def test_price_check_interval_must_be_positive(interval):
    with pytest.raises(ValidationError):
        Settings(price_check_interval=interval)


@pytest.mark.asyncio
@pytest.mark.parametrize("handler", [process_target_price, process_edit_target_price])
@pytest.mark.parametrize("text", [None, "-100", "0", "2147483648"])
async def test_bad_price_does_not_reach_database(handler, text):
    message = MagicMock(text=text, answer=AsyncMock())
    state = AsyncMock()
    state.get_data.return_value = {}
    session = MagicMock()
    await handler(message, state, session)
    message.answer.assert_awaited_once()
    state.clear.assert_not_awaited()
    session.execute.assert_not_called()


def test_date_accepts_whitespace_and_nontext_input():
    assert parse_date(None) is None
    assert parse_date(" 01-01-2027 ").isoformat() == "2027-01-01"
