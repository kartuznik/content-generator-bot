from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.config import Settings
from bot.database import ensure_user
from bot.services.yookassa_client import YooKassaClient


router = Router(name="payment")


def subscribe_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Купить подписку", callback_data="subscribe")]]
    )


async def process_yookassa_webhook(payload: dict, yookassa_client: YooKassaClient) -> dict:
    return await yookassa_client.handle_webhook(payload)


@router.message(Command("subscribe"))
async def subscribe_handler(
    message: Message,
    settings: Settings,
    yookassa_client: YooKassaClient,
) -> None:
    await ensure_user(
        settings.db_path,
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    payment = await yookassa_client.create_payment(user_id=message.from_user.id)
    await message.answer(
        f"Оплатите подписку по ссылке:\n{payment['confirmation_url']}\n\nПосле оплаты доступ активируется автоматически."
    )


@router.callback_query(lambda c: c.data == "subscribe")
async def subscribe_callback_handler(
    callback: CallbackQuery,
    settings: Settings,
    yookassa_client: YooKassaClient,
) -> None:
    await ensure_user(
        settings.db_path,
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    payment = await yookassa_client.create_payment(user_id=callback.from_user.id)
    await callback.message.answer(
        f"Ссылка на оплату:\n{payment['confirmation_url']}\n\nПосле оплаты подписка активируется."
    )
    await callback.answer()
