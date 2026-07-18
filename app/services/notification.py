from datetime import date

from aiogram import Bot


class NotificationService:

    def __init__(self, bot: Bot):
        self.bot = bot

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

        route = (
            f"✈️ {origin} → {destination} "
            f"({departure_date.strftime('%d.%m.%Y')})"
        )

        # Отслеживание без целевой цены
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

        # Есть целевая цена
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

        await self.bot.send_message(
            chat_id=telegram_id,
            text=(
                "😔 Не удалось найти рейсы.\n\n"
                f"✈️ {origin} → {destination} "
                f"({departure_date.strftime('%d.%m.%Y')})"
            ),
        )