from unittest.mock import AsyncMock, MagicMock

import pytest

from app.handlers.help import help_handler, help_callback, HELP_TEXT
from app.keyboards.help import help_keyboard


@pytest.mark.asyncio
async def test_help_command():
    message = MagicMock()
    message.answer = AsyncMock()

    await help_handler(message)

    message.answer.assert_called_once_with(
        HELP_TEXT,
        reply_markup=help_keyboard,
    )


@pytest.mark.asyncio
async def test_help_callback():
    callback = MagicMock()

    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()

    await help_callback(callback)

    callback.message.edit_text.assert_called_once_with(
        HELP_TEXT,
        reply_markup=help_keyboard,
    )

    callback.answer.assert_called_once()