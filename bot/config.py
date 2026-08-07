from dataclasses import dataclass
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(slots=True)
class Settings:
    telegram_bot_token: str
    openai_api_key: str
    openai_model: str
    yokassa_shop_id: str
    yokassa_secret_key: str
    admin_web_password: str
    db_path: str = "data/content_generator.db"
    yookassa_return_url: str = "https://t.me"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            yokassa_shop_id=os.getenv("YOKASSA_SHOP_ID", ""),
            yokassa_secret_key=os.getenv("YOKASSA_SECRET_KEY", ""),
            admin_web_password=os.getenv("ADMIN_WEB_PASSWORD", ""),
            db_path=os.getenv("DB_PATH", "data/content_generator.db"),
            yookassa_return_url=os.getenv("YOOKASSA_RETURN_URL", "https://t.me"),
        )
