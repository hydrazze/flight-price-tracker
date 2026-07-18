from app.repositories.track import TrackRepository
from app.providers.travelpayouts import TravelPayoutsClient
from app.repositories.price_history import PriceHistoryRepository

from app.services.notification import NotificationService


class PriceCheckerService:

    def __init__(
        self,
        repository: TrackRepository,
        client: TravelPayoutsClient,
        notification_service: NotificationService,
        price_history_repository: PriceHistoryRepository,
    ):
        self.repository = repository
        self.client = client
        self.notification_service = notification_service
        self.price_history_repository = price_history_repository


    async def check_prices(self) -> None:

        tracks = await self.repository.get_active_tracks()

        for track in tracks:

            response = await self.client.get_prices_for_dates(
                origin=track.origin,
                destination=track.destination,
                departure_date=track.departure_date,
            )

            if not response.data:

                if not track.no_flights_notified:

                    await self.notification_service.send_no_flights_alert(
                        telegram_id=track.user.telegram_id,
                        origin=track.origin,
                        destination=track.destination,
                        departure_date=track.departure_date,
                    )

                    track.no_flights_notified = True

                    await self.repository.save(track)

                continue

            cheapest_price = min(
                flight.price
                for flight in response.data
            )

            if not track.no_flights_notified:

                track.no_flights_notified = True

                await self.repository.save(track)

                await self.notification_service.send_no_flights_alert(
                    telegram_id=track.user.telegram_id,
                    origin=track.origin,
                    destination=track.destination,
                    departure_date=track.departure_date,
                )

            print(
                f"{track.origin} -> {track.destination}: "
                f"{cheapest_price} руб."
            )

            if (
                track.target_price is not None
                and cheapest_price <= track.target_price
            ):
                await self.notification_service.send_price_alert(
                    telegram_id=track.user.telegram_id,
                    origin=track.origin,
                    destination=track.destination,
                    price=cheapest_price,
                    target_price=track.target_price,
                )

            if track.last_price != cheapest_price:
                await self.repository.update_last_price(
                    track,
                    cheapest_price,
                )
                await self.price_history_repository.create(
                    track_id=track.id,
                    price=cheapest_price,
                )