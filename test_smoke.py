import asyncio
import os

from dotenv import load_dotenv

from bot.services.openai_client import OpenAIClient


async def main() -> None:
    load_dotenv()

    print("🧪 Smoke-тест сервисов Content Generator Bot\n")
    openai_client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY", "dummy_key"))
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # 1. Тест генерации текста (OpenAI GPT)
    print("1️⃣ Тестируем OpenAI GPT (text)...")
    try:
        result = await openai_client.generate_text(
            prompt="Напиши короткий пост про AI в 2 предложениях",
            model=model,
        )
        print(f"✅ OpenAI GPT ответ: {result[:100]}...")
    except Exception as e:  # noqa: BLE001
        print(
            "⚠️ OpenAI GPT ошибка (ожидаемо, если ключ тестовый): "
            f"{type(e).__name__}: {e}"
        )

    # 2. Тест DALL-E 3
    print("\n2️⃣ Тестируем OpenAI DALL-E 3 (image)...")
    try:
        url = await openai_client.generate_image("A cute robot coding in Python")
        print(f"✅ DALL-E 3 URL: {url}")
    except Exception as e:  # noqa: BLE001
        print(
            "⚠️ DALL-E 3 ошибка (ожидаемо, если ключ тестовый): "
            f"{type(e).__name__}: {e}"
        )

    print("\n✅ Smoke-тест завершён!")


if __name__ == "__main__":
    asyncio.run(main())
