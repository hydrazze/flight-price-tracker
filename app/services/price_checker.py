from datetime import datetime, timezone

from app.repositories.track import TrackRepository
from app.providers.travelpayouts import TravelPayoutsClient
from app.repositories.price_history import PriceHistoryRepository

from app.services.notification import NotificationService

from app.models.enums import TrackStatus


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

            try:
                response = await self.client.get_prices_for_dates(
                    origin=track.origin,
                    destination=track.destination,
                    departure_date=track.departure_date,
                )

                track.last_checked_at = datetime.now(timezone.utc)

            except Exception:
                track.status = TrackStatus.ERROR
                track.last_checked_at = datetime.now(timezone.utc)

                continue


            if not response.data:

                track.status = TrackStatus.NOT_FOUND

                if not track.no_flights_notified:

                    await self.notification_service.send_no_flights_alert(
                        telegram_id=track.user.telegram_id,
                        origin=track.origin,
                        destination=track.destination,
                        departure_date=track.departure_date,
                    )

                    track.no_flights_notified = True

                continue


            track.status = TrackStatus.AVAILABLE
            track.no_flights_notified = False


            cheapest_price = min(
                flight.price
                for flight in response.data
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

                await self.price_history_repository.create(
                    track_id=track.id,
                    price=cheapest_price,
                )

                track.last_price = cheapest_price


        await self.repository.save()