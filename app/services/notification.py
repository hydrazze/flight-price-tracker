from datetime import date

from aiogram import Bot


class NotificationService:

    def __init__(
        self,
        bot: Bot,
    ):
        self.bot = bot

    async def send_price_alert(
        self,
        telegram_id: int,
        origin: str,
        destination: str,
        price: int,
        target_price: int,
    ) -> None:

        await self.bot.send_message(
            chat_id=telegram_id,
            text=(
                "✈️ Цена достигла вашей цели!\n\n"
                f"{origin} → {destination}\n"
                f"Текущая цена: {price} ₽\n"
                f"Целевая цена: {target_price} ₽"
            ),
        )

    async def send_no_flights_alert(
        self,
        telegram_id: int,
        origin: str,
        destination: str,
        departure_date: date,
    ) -> None:

        await self.bot.send_message(
            chat_id=telegram_id,
            text=(
                "❌ Рейсы не найдены\n\n"
                f"{origin} → {destination}\n"
                f"Дата: {departure_date}\n\n"
                "Мы продолжим автоматически проверять цены."
            ),
        )

    async def send_flights_available_alert(
        self,
        telegram_id: int,
        origin: str,
        destination: str,
        departure_date: date,
        price: int,
    ) -> None:

        await self.bot.send_message(
            chat_id=telegram_id,
            text=(
                "✈️ Рейсы снова появились!\n\n"
                f"{origin} → {destination}\n"
                f"Дата: {departure_date}\n"
                f"Минимальная цена: {price} ₽"
            ),
        )