from app.repositories.track import TrackRepository
from app.clients.travelpayouts import TravelPayoutsClient


class PriceCheckerService:

    def __init__(
        self,
        repository: TrackRepository,
        client: TravelPayoutsClient,
    ):
        self.repository = repository
        self.client = client


    async def check_prices(self):

        tracks = await self.repository.get_active_tracks()

        for track in tracks:

            response = await self.client.get_prices_for_dates(
                origin=track.origin,
                destination=track.destination,
                departure_date=track.departure_date,
            )

            if not response.data:
                continue

            cheapest_flight = min(
                response.data,
                key=lambda flight: flight.price
            )

            current_price = cheapest_flight.price

            await self.repository.update_last_price(
                track,
                current_price,
            )

            print(
                f"{track.origin}->{track.destination}: "
                f"{current_price} руб."
            )