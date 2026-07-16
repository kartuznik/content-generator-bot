from dataclasses import dataclass
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(slots=True)
class Settings:
    telegram_bot_token: str
    yandex_iam_token: str
    yandex_folder_id: str
    openai_api_key: str
    yokassa_shop_id: str
    yokassa_secret_key: str
    admin_web_password: str
    db_path: str = "data/content_generator.db"
    yookassa_return_url: str = "https://t.me"


def load_settings() -> Settings:
    return Settings(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        yandex_iam_token=os.getenv("YANDEX_IAM_TOKEN", ""),
        yandex_folder_id=os.getenv("YANDEX_FOLDER_ID", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        yokassa_shop_id=os.getenv("YOKASSA_SHOP_ID", ""),
        yokassa_secret_key=os.getenv("YOKASSA_SECRET_KEY", ""),
        admin_web_password=os.getenv("ADMIN_WEB_PASSWORD", ""),
        db_path=os.getenv("DB_PATH", "data/content_generator.db"),
        yookassa_return_url=os.getenv("YOOKASSA_RETURN_URL", "https://t.me"),
    )
