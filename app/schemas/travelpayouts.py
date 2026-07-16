from datetime import datetime

from pydantic import BaseModel


class FlightPrice(BaseModel):
    origin: str
    destination: str

    origin_airport: str
    destination_airport: str

    price: int

    airline: str
    flight_number: str

    departure_at: datetime
    return_at: datetime | None = None

    transfers: int
    return_transfers: int | None = None

    duration: int
    duration_to: int
    duration_back: int | None = None

    expires_at: datetime | None = None
    actual: bool | None = None

    link: str


class PricesForDatesResponse(BaseModel):
    success: bool
    data: list[FlightPrice]
    currency: str