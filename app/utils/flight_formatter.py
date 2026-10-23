from html import escape
from urllib.parse import urlsplit

from pydantic import ValidationError

from app.schemas.travelpayouts import FlightPrice
from app.services.airline_resolver import airline_name


def _offer_url(link: str) -> str | None:
    try:
        parts = urlsplit(link)
        host = parts.hostname
    except ValueError:
        return None
    if parts.path.startswith("/search/"):
        if not parts.scheme and not parts.netloc:
            return "https://www.aviasales.ru" + link
        if (
            parts.scheme == "https"
            and host in {"aviasales.ru", "www.aviasales.ru", "aviasales.com", "www.aviasales.com"}
            and parts.username is None and parts.password is None
        ):
            return link
    return None


def _stops(count: int | None) -> str:
    if count is None or count < 0:
        return "нет данных"
    if count == 0:
        return "без пересадок"
    if count % 10 == 1 and count % 100 != 11:
        unit = "пересадка"
    elif count % 10 in (2, 3, 4) and count % 100 not in (12, 13, 14):
        unit = "пересадки"
    else:
        unit = "пересадок"
    return f"{count} {unit}"


def format_flight_offer(snapshot: dict | None, *, stale: bool = False) -> str:
    if not snapshot:
        return ""
    try:
        flight = FlightPrice.model_validate(snapshot)
    except ValidationError:
        return ""

    title = "Последнее найденное предложение (проверка не удалась)" if stale else "Найденное предложение"
    airline_label = "Авиакомпания (туда)" if flight.return_at else "Авиакомпания"
    lines = [
        f"🔎 {title}",
        f"🏢 {airline_label}: {escape(airline_name(flight.airline))}",
        f"✈️ Рейс туда: {escape(flight.airline)} {escape(flight.flight_number)}",
        f"🛫 Туда: {escape(flight.origin_airport)} → {escape(flight.destination_airport)}",
        f"🕓 Вылет туда: {flight.departure_at.strftime('%d.%m.%Y %H:%M')} (местное время)",
        f"🔀 Туда: {_stops(flight.transfers)}",
    ]
    if flight.return_at is not None:
        lines += [
            f"🕓 Вылет обратно: {flight.return_at.strftime('%d.%m.%Y %H:%M')} (местное время)",
            f"🔀 Обратно: {_stops(flight.return_transfers)}",
        ]
    if flight.transfers > 0 or (flight.return_transfers or 0) > 0:
        lines.append("Аэропорты пересадок: нет данных от источника.")
    url = _offer_url(flight.link)
    if url:
        lines.append(f'<a href="{escape(url, quote=True)}">Открыть маршрут и детали билета</a>')
    return "\n".join(lines)
