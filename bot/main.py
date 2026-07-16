import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import load_settings
from bot.database import init_db
from bot.handlers.commands import router as commands_router
from bot.handlers.payment import router as payment_router
from bot.middlewares.ban_check import BanCheckMiddleware
from bot.middlewares.usage_limit import UsageLimitMiddleware
from bot.services.dalle_client import DALLEClient
from bot.services.yandex_gpt import YandexGPTClient
from bot.services.yookassa_client import YooKassaClient


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = load_settings()
    await init_db(settings.db_path)

    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    yandex_client = YandexGPTClient(
        iam_token=settings.yandex_iam_token, folder_id=settings.yandex_folder_id
    )
    dalle_client = DALLEClient(api_key=settings.openai_api_key)
    yookassa_client = YooKassaClient(
        shop_id=settings.yokassa_shop_id,
        secret_key=settings.yokassa_secret_key,
        return_url=settings.yookassa_return_url,
        db_path=settings.db_path,
    )

    dp["settings"] = settings
    dp["yandex_client"] = yandex_client
    dp["dalle_client"] = dalle_client
    dp["yookassa_client"] = yookassa_client

    dp.message.middleware(BanCheckMiddleware(settings.db_path))
    dp.callback_query.middleware(BanCheckMiddleware(settings.db_path))
    dp.message.middleware(UsageLimitMiddleware(settings.db_path))

    dp.include_router(commands_router)
    dp.include_router(payment_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
