from __future__ import annotations

from typing import Awaitable, Callable

from aiogram import Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message

from bot.config import Settings
from bot.database import (
    ensure_user,
    get_usage,
    increment_image_generation,
    increment_text_generation,
)
from bot.services.dalle_client import DALLEClient
from bot.services.yandex_gpt import YandexGPTClient


router = Router(name="commands")


@router.message(CommandStart())
async def start_handler(message: Message, settings: Settings) -> None:
    await ensure_user(
        settings.db_path,
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    usage = await get_usage(settings.db_path, message.from_user.id)
    await message.answer(
        (
            "Привет! Я Content Generator.\n\n"
            "Текст генерирую через YandexGPT, изображения — через DALL-E 3.\n"
            "Команды:\n"
            "/generate <тема>\n"
            "/generate_image <описание>\n"
            "/subscribe\n"
            "/help\n\n"
            f"Бесплатных генераций осталось: {usage['free_generations_left']}"
        )
    )


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(
        (
            "/start — регистрация и приветствие\n"
            "/generate <текст> — сгенерировать пост через YandexGPT\n"
            "/generate_image <описание> — сгенерировать картинку через DALL-E 3\n"
            "/subscribe — оформить подписку через YooKassa\n"
            "/help — помощь"
        )
    )


@router.message(Command("generate"))
async def generate_handler(
    message: Message,
    command: CommandObject,
    settings: Settings,
    yandex_client: YandexGPTClient,
    mark_generation_success: Callable[[], Awaitable[None]] | None = None,
) -> None:
    await ensure_user(
        settings.db_path,
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    prompt = (command.args or "").strip()
    if not prompt:
        await message.answer("Использование: /generate <тема или задача>")
        return
    await message.answer("Генерирую текст через YandexGPT...")
    try:
        text = await yandex_client.generate_text(prompt)
    except Exception:
        await message.answer("Не удалось сгенерировать текст. Попробуйте позже.")
        return

    await increment_text_generation(settings.db_path, message.from_user.id)
    if mark_generation_success:
        await mark_generation_success()
    usage = await get_usage(settings.db_path, message.from_user.id)
    await message.answer(f"{text}\n\nОсталось бесплатных генераций: {usage['free_generations_left']}")


@router.message(Command("generate_image"))
async def generate_image_handler(
    message: Message,
    command: CommandObject,
    settings: Settings,
    dalle_client: DALLEClient,
    mark_generation_success: Callable[[], Awaitable[None]] | None = None,
) -> None:
    await ensure_user(
        settings.db_path,
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    prompt = (command.args or "").strip()
    if not prompt:
        await message.answer("Использование: /generate_image <описание изображения>")
        return
    await message.answer("Генерирую изображение через DALL-E 3...")
    try:
        image_url = await dalle_client.generate_image(prompt)
    except Exception:
        await message.answer("Не удалось сгенерировать изображение. Попробуйте позже.")
        return

    await increment_image_generation(settings.db_path, message.from_user.id)
    if mark_generation_success:
        await mark_generation_success()
    usage = await get_usage(settings.db_path, message.from_user.id)
    await message.answer(
        f"Готово: {image_url}\n\nОсталось бесплатных генераций: {usage['free_generations_left']}"
    )
