from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.config import Settings
from bot.database import ensure_user, get_usage
from bot.services.yookassa_client import YooKassaClient


router = Router(name="commands")

TARIFFS = {
    "week": {"label": "Неделя - 299₽", "amount": 299.0, "days": 7},
    "month": {"label": "Месяц - 799₽", "amount": 799.0, "days": 30},
}


def generation_entry_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Начать генерацию", callback_data="start_generation")]
        ]
    )


def subscribe_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=TARIFFS["week"]["label"],
                    callback_data="subscribe_plan:week",
                )
            ],
            [
                InlineKeyboardButton(
                    text=TARIFFS["month"]["label"],
                    callback_data="subscribe_plan:month",
                )
            ],
        ]
    )


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
            "Я умею генерировать:\n"
            "- тексты через YandexGPT\n"
            "- изображения через DALL-E 3\n\n"
            "Команды:\n"
            "/generate <текст>\n"
            "/generate_image <описание>\n"
            "/subscribe\n"
            "/help\n\n"
            f"Бесплатных генераций осталось: {usage['free_generations_left']}"
        ),
        reply_markup=generation_entry_keyboard(),
    )


@router.callback_query(F.data == "start_generation")
async def start_generation_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(generation_mode=True)
    if callback.message:
        await callback.message.answer(
            "Режим генерации включен. Отправьте текст сообщением или используйте /generate <текст>."
        )
    await callback.answer()


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(
        (
            "Доступные команды:\n"
            "/start - приветствие и запуск\n"
            "/generate <текст> - генерация текста\n"
            "/generate_image <описание> - генерация изображения\n"
            "/subscribe - выбор тарифа и оплата подписки\n"
            "/help - справка"
        )
    )


@router.message(Command("subscribe"))
async def subscribe_handler(message: Message) -> None:
    await message.answer(
        "Выберите тариф подписки:",
        reply_markup=subscribe_keyboard(),
    )


@router.callback_query(F.data.startswith("subscribe_plan:"))
async def subscribe_plan_callback(
    callback: CallbackQuery,
    settings: Settings,
    yookassa_client: YooKassaClient,
) -> None:
    if callback.from_user is None:
        await callback.answer()
        return

    await ensure_user(
        settings.db_path,
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )

    tariff_key = callback.data.split(":", maxsplit=1)[1]
    tariff = TARIFFS.get(tariff_key)
    if not tariff:
        await callback.answer("Неизвестный тариф", show_alert=True)
        return

    payment = await yookassa_client.create_payment(
        user_id=callback.from_user.id,
        amount=float(tariff["amount"]),
        description=f"Подписка Content Generator: {tariff['label']}",
        subscription_days=int(tariff["days"]),
    )

    if callback.message:
        await callback.message.answer(
            (
                f"Тариф: {tariff['label']}\n"
                f"Ссылка на оплату: {payment['confirmation_url']}\n\n"
                "После успешной оплаты подписка активируется автоматически."
            )
        )
    await callback.answer()
