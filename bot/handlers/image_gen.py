from __future__ import annotations

from typing import Any, Awaitable, Callable

import httpx
from aiogram import Router
from aiogram.filters import Command, CommandObject, Filter
from aiogram.types import BufferedInputFile, Message

from bot.config import Settings
from bot.database import ensure_user, increment_image_generation, save_generated_post
from bot.services.dalle_client import DALLEClient


router = Router(name="image_gen")


class GenerationContextFilter(Filter):
    async def __call__(self, *args: Any, **kwargs: Any) -> dict[str, bool]:
        return {"is_generation": True}


@router.message(
    Command("generate_image"),
    GenerationContextFilter(),
    flags={"is_generation": True},
)
async def generate_image_handler(
    message: Message,
    command: CommandObject,
    settings: Settings,
    dalle_client: DALLEClient,
    mark_generation_success: Callable[[], Awaitable[None]] | None = None,
) -> None:
    prompt = (command.args or "").strip()
    if not prompt:
        await message.answer("Использование: /generate_image <описание изображения>")
        return

    await ensure_user(
        settings.db_path,
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    await message.answer("Генерирую изображение через DALL-E 3...")

    try:
        image_url = await dalle_client.generate_image(prompt)
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(image_url)
            response.raise_for_status()
            image_content = response.content
    except Exception as exc:  # noqa: BLE001
        await save_generated_post(
            db_path=settings.db_path,
            user_id=message.from_user.id,
            generation_type="image",
            prompt=prompt,
            result=None,
            generation_succeeded=False,
            error_message=f"{type(exc).__name__}: {exc}",
        )
        await message.answer("Ошибка генерации изображения. Попробуйте позже.")
        return

    await increment_image_generation(settings.db_path, message.from_user.id)
    await save_generated_post(
        db_path=settings.db_path,
        user_id=message.from_user.id,
        generation_type="image",
        prompt=prompt,
        result=image_url,
        generation_succeeded=True,
    )
    if mark_generation_success:
        await mark_generation_success()

    photo = BufferedInputFile(image_content, filename="generated_image.png")
    await message.answer_photo(
        photo=photo,
        caption=f"Готово. Источник: {image_url}",
    )
