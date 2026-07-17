from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import Router
from aiogram.filters import Command, CommandObject, Filter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.config import Settings
from bot.database import ensure_user, increment_text_generation, save_generated_post
from bot.services.yandex_gpt import YandexGPTClient


router = Router(name="text_gen")


class GenerationContextFilter(Filter):
    async def __call__(self, *args: Any, **kwargs: Any) -> dict[str, bool]:
        return {"is_generation": True}


class GenerationModeTextFilter(Filter):
    async def __call__(self, message: Message, state: FSMContext) -> bool | dict[str, bool]:
        if not message.text or message.text.startswith("/"):
            return False
        state_data = await state.get_data()
        if not state_data.get("generation_mode", False):
            return False
        return {"is_generation": True}


async def _generate_text_and_respond(
    *,
    message: Message,
    prompt: str,
    settings: Settings,
    yandex_client: YandexGPTClient,
    mark_generation_success: Callable[[], Awaitable[None]] | None,
) -> None:
    await ensure_user(
        settings.db_path,
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    await message.answer("Генерирую текст через YandexGPT...")
    try:
        generated_text = await yandex_client.generate_text(prompt)
    except Exception as exc:  # noqa: BLE001
        await save_generated_post(
            db_path=settings.db_path,
            user_id=message.from_user.id,
            generation_type="text",
            prompt=prompt,
            result=None,
            generation_succeeded=False,
            error_message=f"{type(exc).__name__}: {exc}",
        )
        await message.answer(
            "Ошибка генерации текста. Попробуйте позже или уточните запрос."
        )
        return

    await increment_text_generation(settings.db_path, message.from_user.id)
    await save_generated_post(
        db_path=settings.db_path,
        user_id=message.from_user.id,
        generation_type="text",
        prompt=prompt,
        result=generated_text,
        generation_succeeded=True,
    )
    if mark_generation_success:
        await mark_generation_success()
    await message.answer(generated_text)


@router.message(Command("generate"), GenerationContextFilter(), flags={"is_generation": True})
async def generate_command_handler(
    message: Message,
    command: CommandObject,
    settings: Settings,
    yandex_client: YandexGPTClient,
    mark_generation_success: Callable[[], Awaitable[None]] | None = None,
) -> None:
    prompt = (command.args or "").strip()
    if not prompt:
        await message.answer("Использование: /generate <ваш запрос>")
        return

    await _generate_text_and_respond(
        message=message,
        prompt=prompt,
        settings=settings,
        yandex_client=yandex_client,
        mark_generation_success=mark_generation_success,
    )


@router.message(GenerationModeTextFilter(), flags={"is_generation": True})
async def generate_text_message_handler(
    message: Message,
    settings: Settings,
    yandex_client: YandexGPTClient,
    mark_generation_success: Callable[[], Awaitable[None]] | None = None,
) -> None:
    prompt = (message.text or "").strip()
    if not prompt:
        return

    await _generate_text_and_respond(
        message=message,
        prompt=prompt,
        settings=settings,
        yandex_client=yandex_client,
        mark_generation_success=mark_generation_success,
    )
