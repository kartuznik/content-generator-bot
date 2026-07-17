from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    TelegramObject,
)

from bot.database import decrement_free_generation, get_usage


class UsageLimitMiddleware(BaseMiddleware):
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user is None:
            return await handler(event, data)

        is_generation = bool(data.get("is_generation", False))
        if not is_generation:
            handler_obj = data.get("handler")
            flags = getattr(handler_obj, "flags", {}) if handler_obj else {}
            is_generation = bool(flags.get("is_generation", False))

        if not is_generation:
            return await handler(event, data)

        usage = await get_usage(self.db_path, user.id)
        free_generations_left = int(usage.get("free_generations_left", 0))
        is_subscribed = bool(usage.get("is_subscribed", False))

        if is_subscribed or free_generations_left > 0:
            data["generation_succeeded"] = False

            async def mark_generation_success() -> None:
                data["generation_succeeded"] = True

            data["mark_generation_success"] = mark_generation_success
            result = await handler(event, data)
            generation_succeeded = bool(data.get("generation_succeeded", False))
            if not is_subscribed and generation_succeeded:
                await decrement_free_generation(self.db_path, user.id)
            return result

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💳 Оформить подписку",
                        callback_data="subscribe",
                    )
                ]
            ]
        )
        message_text = (
            "У вас закончились бесплатные генерации. "
            "Оформите подписку, чтобы продолжить."
        )

        if isinstance(event, Message):
            await event.answer(message_text, reply_markup=keyboard)
            return
        if isinstance(event, CallbackQuery):
            if event.message:
                await event.message.answer(message_text, reply_markup=keyboard)
            await event.answer()
            return

        return
