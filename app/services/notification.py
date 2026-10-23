from datetime import date

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError

from app.logging.logger import logger
from app.models.enums import StopPreference
from app.utils.track_formatter import format_itinerary
from app.utils.flight_formatter import format_flight_offer


class NotificationService:

    def __init__(self, bot: Bot):
        self.bot = bot

    async def _send_message(
        self,
        telegram_id: int,
        text: str,
    ) -> None:
        try:
            await self.bot.send_message(
                chat_id=telegram_id,
                text=text,
            )
        except TelegramForbiddenError:
            logger.warning(
                f"User {telegram_id} blocked the bot"
            )

    def _format_route(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: date | None = None,
        stop_preference: StopPreference = StopPreference.ANY,
    ) -> str:
        return format_itinerary(
            origin, destination, departure_date, return_date, stop_preference,
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
        return_date: date | None = None,
        stop_preference: StopPreference = StopPreference.ANY,
        offer: dict | None = None,
    ) -> None:

        route = self._format_route(origin, destination, departure_date, return_date, stop_preference)

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

        if return_date is not None:
            text += "\n\nЦена за всю поездку туда и обратно."

        details = format_flight_offer(offer)
        if details:
            text += "\n\n" + details

        await self._send_message(
            telegram_id=telegram_id,
            text=text,
        )

    async def send_no_flights_alert(
        self,
        telegram_id: int,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: date | None = None,
        stop_preference: StopPreference = StopPreference.ANY,
    ) -> None:

        route = self._format_route(origin, destination, departure_date, return_date, stop_preference)

        await self._send_message(
            telegram_id=telegram_id,
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
        return_date: date | None = None,
        stop_preference: StopPreference = StopPreference.ANY,
    ) -> None:

        route = self._format_route(origin, destination, departure_date, return_date, stop_preference)

        await self._send_message(
            telegram_id=telegram_id,
            text=(
                "🛫 Отслеживание завершено\n\n"
                f"{route}\n\n"
                "Дата вылета туда уже прошла.\n"
                "Отслеживание автоматически отключено."
            ),
        )