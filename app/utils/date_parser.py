from datetime import datetime, date


def parse_date(value: str) -> date | None:
    formats = [
        "%d-%m-%Y",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None
