import asyncio
import os

from dotenv import load_dotenv

from bot.services.dalle_client import DALLEClient
from bot.services.yandex_gpt import YandexGPTClient


async def main() -> None:
    load_dotenv()

    print("🧪 Smoke-тест сервисов Content Generator Bot\n")

    # 1. Тест YandexGPT
    print("1️⃣ Тестируем YandexGPT...")
    yandex_client = YandexGPTClient(
        iam_token=os.getenv("YANDEX_IAM_TOKEN", "dummy_token"),
        folder_id=os.getenv("YANDEX_FOLDER_ID", "dummy_folder"),
    )
    try:
        result = await yandex_client.generate_text(
            "Напиши короткий пост про AI в 2 предложениях"
        )
        print(f"✅ YandexGPT ответ: {result[:100]}...")
    except Exception as e:  # noqa: BLE001
        print(
            "⚠️ YandexGPT ошибка (ожидаемо, если токены тестовые): "
            f"{type(e).__name__}: {e}"
        )

    # 2. Тест DALL-E 3
    print("\n2️⃣ Тестируем DALL-E 3...")
    dalle_client = DALLEClient(api_key=os.getenv("OPENAI_API_KEY", "dummy_key"))
    try:
        url = await dalle_client.generate_image("A cute robot coding in Python")
        print(f"✅ DALL-E 3 URL: {url}")
    except Exception as e:  # noqa: BLE001
        print(
            "⚠️ DALL-E 3 ошибка (ожидаемо, если ключ тестовый): "
            f"{type(e).__name__}: {e}"
        )

    print("\n✅ Smoke-тест завершён!")


if __name__ == "__main__":
    asyncio.run(main())
