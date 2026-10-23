from datetime import datetime, timezone
from zoneinfo import ZoneInfo


MOSCOW = ZoneInfo("Europe/Moscow")


def format_moscow_time(value: datetime) -> str:
    # SQLite can return a naive datetime for a UTC column.
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(MOSCOW).strftime("%d.%m.%Y %H:%M") + " МСК"
