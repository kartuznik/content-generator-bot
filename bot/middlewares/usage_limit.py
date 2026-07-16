from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, TelegramObject

from bot.database import decrement_free_generation, get_usage


LIMITED_COMMANDS = ("/generate", "/generate_image")


class UsageLimitMiddleware(BaseMiddleware):
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or not event.text:
            return await handler(event, data)

        text = event.text.strip()
        if not text.startswith(LIMITED_COMMANDS):
            return await handler(event, data)

        user_id = event.from_user.id
        usage = await get_usage(self.db_path, user_id)
        subscribed = bool(usage.get("is_subscribed"))
        free_left = int(usage.get("free_generations_left", 0))
        has_payload = len(text.split(maxsplit=1)) > 1

        if not subscribed and free_left <= 0:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Купить подписку", callback_data="subscribe")]
                ]
            )
            await event.answer(
                "Бесплатный лимит генераций исчерпан. Оформите подписку командой /subscribe.",
                reply_markup=keyboard,
            )
            return None

        data["generation_succeeded"] = False

        async def mark_generation_success() -> None:
            data["generation_succeeded"] = True

        data["mark_generation_success"] = mark_generation_success
        result = await handler(event, data)

        if not subscribed and has_payload and data.get("generation_succeeded"):
            await decrement_free_generation(self.db_path, user_id)

        return result
