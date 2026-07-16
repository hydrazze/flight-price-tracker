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
                "✈️ Цена снизилась!\n\n"
                f"{origin} → {destination}\n"
                f"Цена: {price} руб.\n"
                f"Целевая цена: {target_price} руб."
            ),
        )