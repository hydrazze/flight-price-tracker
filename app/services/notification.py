from datetime import date

from aiogram import Bot

from app.services.city_resolver import resolver


class NotificationService:

    def __init__(self, bot: Bot):
        self.bot = bot

    def _format_route(self, origin: str, destination: str, departure_date: date) -> str:
        origin_name = resolver.get_city_name(origin)
        destination_name = resolver.get_city_name(destination)

        return (
            f"✈️ {origin_name} ({origin.upper()}) → {destination_name} ({destination.upper()})\n"
            f"📅 {departure_date.strftime('%d.%m.%Y')}"
        )

    async def send_price_alert(
        self,
        telegram_id: int,
        origin: str,
        destination: str,
        departure_date: date,
        old_price: int | None,
        new_price: int,
        target_price: int | None,
    ) -> None:

        route = self._format_route(origin, destination, departure_date)

        if target_price is None:
            text = (
                "💸 Цена изменилась!\n\n"
                f"{route}\n\n"
            )

            if old_price is not None:
                if new_price < old_price:
                    text += (
                        f"⬇️ Было: {old_price} ₽\n"
                        f"💰 Стало: {new_price} ₽"
                    )
                elif new_price > old_price:
                    text += (
                        f"⬆️ Было: {old_price} ₽\n"
                        f"💰 Стало: {new_price} ₽"
                    )
                else:
                    text += (
                        f"💰 Цена: {new_price} ₽"
                    )
            else:
                text += (
                    f"💰 Цена: {new_price} ₽"
                )

        else:
            if new_price <= target_price:
                title = "🎯 Цена достигла вашей цели!"
            else:
                title = "📈 Цена снова выше вашей цели"

            text = (
                f"{title}\n\n"
                f"{route}\n\n"
            )

            if old_price is not None:
                if new_price < old_price:
                    text += (
                        f"⬇️ Было: {old_price} ₽\n"
                    )
                elif new_price > old_price:
                    text += (
                        f"⬆️ Было: {old_price} ₽\n"
                    )

            text += (
                f"💰 Стало: {new_price} ₽\n"
                f"🎯 Ваша цель: {target_price} ₽"
            )

        await self.bot.send_message(
            chat_id=telegram_id,
            text=text,
        )

    async def send_no_flights_alert(
        self,
        telegram_id: int,
        origin: str,
        destination: str,
        departure_date: date,
    ) -> None:

        route = self._format_route(origin, destination, departure_date)

        await self.bot.send_message(
            chat_id=telegram_id,
            text=(
                "😔 Не удалось найти рейсы.\n\n"
                f"{route}"
            ),
        )

    async def send_track_expired_alert(
        self,
        telegram_id: int,
        origin: str,
        destination: str,
        departure_date: date,
    ) -> None:

        route = self._format_route(origin, destination, departure_date)

        await self.bot.send_message(
            chat_id=telegram_id,
            text=(
                "🛫 Отслеживание завершено\n\n"
                f"{route}\n\n"
                "Рейс уже состоялся.\n"
                "Отслеживание автоматически отключено."
            ),
        )