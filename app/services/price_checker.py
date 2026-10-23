from datetime import datetime, timezone, date

from app.repositories.track import TrackRepository
from app.providers.travelpayouts import TravelPayoutsClient
from app.repositories.price_history import PriceHistoryRepository

from app.services.notification import NotificationService
from app.models.enums import TrackStatus

from app.logging.logger import logger


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


    def should_notify(
        self,
        old_price: int | None,
        new_price: int,
        target_price: int | None,
    ) -> bool:

        if target_price is None:

            if old_price is None:
                return True

            return old_price != new_price


        # Первый найденный рейс
        if old_price is None:
            return new_price <= target_price


        # Цена впервые достигла цели
        if old_price > target_price >= new_price:
            return True


        return False



    async def check_prices(
        self,
        telegram_id: int | None = None,
    ) -> None:

        logger.info(
            "Checking active tracks started"
        )


        expired_tracks = await self.repository.archive_expired_tracks(
            today=date.today(),
            telegram_id=telegram_id,
        )


        for track in expired_tracks:

            await self.notification_service.send_track_expired_alert(
                telegram_id=track.user.telegram_id,
                origin=track.origin,
                destination=track.destination,
                departure_date=track.departure_date,
                return_date=track.return_date,
                stop_preference=track.stop_preference,
            )


        tracks = (
            await self.repository.get_active_tracks()
            if telegram_id is None
            else await self.repository.get_user_tracks(telegram_id)
        )


        logger.info(
            f"Found {len(tracks)} active tracks"
        )


        for track in tracks:

            await self._check_track(
                track
            )


        await self.repository.save()


        logger.info(
            "Checking active tracks finished"
        )



    async def check_one_track(
        self,
        track_id: int,
    ) -> None:

        track = await self.repository.get_by_id(
            track_id
        )


        if track is None:

            logger.warning(
                f"Track #{track_id} not found"
            )

            return


        await self._check_track(
            track
        )


        await self.repository.save()



    async def _check_track(
        self,
        track,
    ) -> None:

        try:

            logger.info(
                f"Checking track #{track.id}"
            )


            response = await self.client.get_prices_for_dates(
                origin=track.origin,
                destination=track.destination,
                departure_date=track.departure_date,
                return_date=track.return_date,
                stop_preference=track.stop_preference,
            )


            if not response.data:

                track.last_offer = None
                track.status = TrackStatus.NOT_FOUND

                track.last_checked_at = datetime.now(
                    timezone.utc
                )


                if not track.no_flights_notified:

                    await self.notification_service.send_no_flights_alert(
                        telegram_id=track.user.telegram_id,
                        origin=track.origin,
                        destination=track.destination,
                        departure_date=track.departure_date,
                        return_date=track.return_date,
                        stop_preference=track.stop_preference,
                    )

                    track.no_flights_notified = True


                logger.info(
                    f"No flights found for track #{track.id}"
                )

                return



            cheapest_flight = min(response.data, key=lambda flight: flight.price)
            cheapest_price = cheapest_flight.price


            old_price = track.last_price


            track.no_flights_notified = False

            track.status = TrackStatus.AVAILABLE

            track.last_checked_at = datetime.now(
                timezone.utc
            )


            offer = cheapest_flight.model_dump(mode="json")

            if self.should_notify(
                old_price=old_price,
                new_price=cheapest_price,
                target_price=track.target_price,
            ):
                await self.notification_service.send_price_alert(
                    telegram_id=track.user.telegram_id,
                    origin=track.origin,
                    destination=track.destination,
                    departure_date=track.departure_date,
                    return_date=track.return_date,
                    stop_preference=track.stop_preference,
                    old_price=old_price,
                    new_price=cheapest_price,
                    target_price=track.target_price,
                    offer=offer,
                )

            if old_price != cheapest_price:
                await self.price_history_repository.create(
                    track_id=track.id,
                    price=cheapest_price,
                )

            # Keep price and details together; failed notifications can retry next check.
            # Refresh details even when a different airline has the same fare.
            track.last_price = cheapest_price
            track.last_offer = offer

            logger.info(
                f"Track #{track.id} checked. Price: {cheapest_price}"
            )


        except Exception:

            logger.exception(
                f"Track check error #{track.id}"
            )


            track.status = TrackStatus.ERROR

            track.last_checked_at = datetime.now(
                timezone.utc
            )
