from unittest.mock import AsyncMock, MagicMock

import pytest

from app import main as application


@pytest.mark.asyncio
async def test_initial_telegram_failure_closes_resources(monkeypatch):
    monkeypatch.setattr(application, "dispatcher", MagicMock())
    monkeypatch.setattr(application, "set_bot_commands", AsyncMock(side_effect=RuntimeError("unavailable")))
    shutdown = AsyncMock()
    monkeypatch.setattr(application, "shutdown", shutdown)
    with pytest.raises(RuntimeError, match="unavailable"):
        await application.main()
    shutdown.assert_awaited_once()
