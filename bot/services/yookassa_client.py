from __future__ import annotations

from datetime import datetime, timezone
import uuid

from yookassa import Configuration, Payment

from bot.database import activate_subscription, save_or_update_payment


class YooKassaClient:
    def __init__(self, shop_id: str, secret_key: str, return_url: str, db_path: str):
        Configuration.account_id = shop_id
        Configuration.secret_key = secret_key
        self.return_url = return_url
        self.db_path = db_path

    async def create_payment(
        self, user_id: int, amount: float = 299.0, description: str = "Подписка на Content Generator"
    ) -> dict[str, str]:
        idempotence_key = str(uuid.uuid4())
        payment = Payment.create(
            {
                "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
                "confirmation": {"type": "redirect", "return_url": self.return_url},
                "capture": True,
                "description": description,
                "metadata": {"user_id": str(user_id)},
            },
            idempotence_key,
        )
        await save_or_update_payment(
            db_path=self.db_path,
            payment_id=payment.id,
            user_id=user_id,
            amount=float(payment.amount.value),
            status=payment.status,
        )
        return {
            "payment_id": payment.id,
            "confirmation_url": payment.confirmation.confirmation_url,
            "status": payment.status,
        }

    async def handle_webhook(self, payload: dict) -> dict[str, str | bool]:
        event = payload.get("event")
        payment_obj = payload.get("object", {})
        payment_id = payment_obj.get("id")
        status = payment_obj.get("status", "unknown")
        metadata = payment_obj.get("metadata", {})
        amount = float(payment_obj.get("amount", {}).get("value", 0))

        user_id_raw = metadata.get("user_id")
        if payment_id and user_id_raw:
            user_id = int(user_id_raw)
            await save_or_update_payment(self.db_path, payment_id, user_id, amount, status)
            if event == "payment.succeeded" or status == "succeeded":
                expires_at = await activate_subscription(self.db_path, user_id, days=30)
                return {
                    "ok": True,
                    "message": "subscription_activated",
                    "subscription_expires_at": expires_at.astimezone(timezone.utc).isoformat(),
                }

        return {"ok": True, "message": "webhook_processed", "received_at": datetime.now(timezone.utc).isoformat()}
