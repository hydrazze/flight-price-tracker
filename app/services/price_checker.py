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



    def should_notify(
        self,
        old_price: int | None,
        new_price: int,
        target_price: int | None,
    ) -> bool:


        # Нет целевой цены:
        # любое изменение цены

        if target_price is None:

            if old_price is None:
                return True

            return old_price != new_price



        # Есть цель

        if old_price is None:

            return new_price <= target_price



        # Было ниже цели
        if old_price <= target_price:

            return True



        # Стало ниже цели
        if new_price <= target_price:

            return True



        # Например:
        # 9000 -> 10000
        return False




    async def check_prices(self) -> None:


        expired_tracks = await self.repository.deactivate_expired_tracks()


        for track in expired_tracks:

            await self.notification_service.send_track_expired_alert(
                telegram_id=track.user.telegram_id,
                origin=track.origin,
                destination=track.destination,
                departure_date=track.departure_date,
            )


        tracks = await self.repository.get_active_tracks()


        for track in tracks:

            await self._check_track(
                track
            )


        await self.repository.save_all(
            tracks
        )



    async def check_one_track(
        self,
        track_id: int,
    ) -> None:


        track = await self.repository.get_by_id(
            track_id
        )


        if track is None:

            return



        await self._check_track(
            track
        )


        await self.repository.save_all(
            [track]
        )



    async def _check_track(
        self,
        track,
    ) -> None:


        try:


            response = await self.client.get_prices_for_dates(

                origin=track.origin,

                destination=track.destination,

                departure_date=track.departure_date,

            )



            if not response.data:


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

                    )


                    track.no_flights_notified = True



                return




            cheapest_price = min(

                flight.price

                for flight in response.data

            )



            old_price = track.last_price



            track.status = TrackStatus.AVAILABLE


            track.last_checked_at = datetime.now(
                timezone.utc
            )




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

                    old_price=old_price,

                    new_price=cheapest_price,

                    target_price=track.target_price,

                )




            if old_price != cheapest_price:


                track.last_price = cheapest_price



                await self.price_history_repository.create(

                    track_id=track.id,

                    price=cheapest_price,

                )



        except Exception:


            track.status = TrackStatus.ERROR


            track.last_checked_at = datetime.now(
                timezone.utc
            )