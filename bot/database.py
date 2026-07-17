from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import aiosqlite


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def init_db(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS user_usage (
                user_id INTEGER PRIMARY KEY,
                text_generations_count INTEGER DEFAULT 0,
                image_generations_count INTEGER DEFAULT 0,
                free_generations_left INTEGER DEFAULT 3,
                subscription_expires_at DATETIME,
                is_subscribed BOOLEAN DEFAULT FALSE,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS banned_users (
                user_id INTEGER PRIMARY KEY,
                reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id TEXT UNIQUE,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                status TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS generated_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                generation_type TEXT NOT NULL,
                prompt TEXT NOT NULL,
                result TEXT,
                generation_succeeded BOOLEAN DEFAULT FALSE,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
            """
        )
        await db.commit()


async def ensure_user(
    db_path: str, user_id: int, username: str | None, first_name: str | None
) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name
            """,
            (user_id, username, first_name),
        )
        await db.execute(
            """
            INSERT INTO user_usage (user_id)
            VALUES (?)
            ON CONFLICT(user_id) DO NOTHING
            """,
            (user_id,),
        )
        await db.commit()


async def is_user_banned(db_path: str, user_id: int) -> bool:
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT 1 FROM banned_users WHERE user_id = ? LIMIT 1", (user_id,)
        )
        return await cursor.fetchone() is not None


async def get_usage(db_path: str, user_id: int) -> dict[str, Any]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM user_usage WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            await db.execute("INSERT INTO user_usage (user_id) VALUES (?)", (user_id,))
            await db.commit()
            return {
                "user_id": user_id,
                "text_generations_count": 0,
                "image_generations_count": 0,
                "free_generations_left": 3,
                "subscription_expires_at": None,
                "is_subscribed": False,
            }
        usage = dict(row)
    if usage["is_subscribed"] and usage["subscription_expires_at"]:
        expires_at = datetime.fromisoformat(usage["subscription_expires_at"])
        if expires_at <= _utc_now():
            await set_subscription_status(db_path, user_id, False, None)
            usage["is_subscribed"] = False
            usage["subscription_expires_at"] = None
    return usage


async def increment_text_generation(db_path: str, user_id: int) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            UPDATE user_usage
            SET text_generations_count = text_generations_count + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (user_id,),
        )
        await db.commit()


async def increment_image_generation(db_path: str, user_id: int) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            UPDATE user_usage
            SET image_generations_count = image_generations_count + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (user_id,),
        )
        await db.commit()


async def decrement_free_generation(db_path: str, user_id: int) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            UPDATE user_usage
            SET free_generations_left = CASE
                    WHEN free_generations_left > 0 THEN free_generations_left - 1
                    ELSE 0
                END,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (user_id,),
        )
        await db.commit()


async def set_subscription_status(
    db_path: str, user_id: int, is_subscribed: bool, expires_at: datetime | None
) -> None:
    expires = expires_at.isoformat() if expires_at else None
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            UPDATE user_usage
            SET is_subscribed = ?,
                subscription_expires_at = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (is_subscribed, expires, user_id),
        )
        await db.commit()


async def activate_subscription(db_path: str, user_id: int, days: int = 30) -> datetime:
    usage = await get_usage(db_path, user_id)
    now = _utc_now()
    current_expiry_raw = usage.get("subscription_expires_at")
    if current_expiry_raw:
        current_expiry = datetime.fromisoformat(current_expiry_raw)
        start_point = current_expiry if current_expiry > now else now
    else:
        start_point = now
    new_expiry = start_point + timedelta(days=days)
    await set_subscription_status(db_path, user_id, True, new_expiry)
    return new_expiry


async def add_free_generations(db_path: str, user_id: int, amount: int) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            UPDATE user_usage
            SET free_generations_left = free_generations_left + ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (amount, user_id),
        )
        await db.commit()


async def list_users_with_usage(db_path: str) -> list[dict[str, Any]]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT
                u.user_id,
                u.username,
                u.first_name,
                uu.text_generations_count,
                uu.image_generations_count,
                uu.free_generations_left,
                uu.subscription_expires_at,
                uu.is_subscribed
            FROM users u
            LEFT JOIN user_usage uu ON uu.user_id = u.user_id
            ORDER BY u.created_at DESC
            """
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_dashboard_stats(db_path: str) -> dict[str, Any]:
    async with aiosqlite.connect(db_path) as db:
        users_count_cursor = await db.execute("SELECT COUNT(*) FROM users")
        active_subs_cursor = await db.execute(
            """
            SELECT COUNT(*)
            FROM user_usage
            WHERE is_subscribed = 1
              AND (subscription_expires_at IS NULL OR subscription_expires_at > ?)
            """,
            (_utc_now().isoformat(),),
        )
        generations_cursor = await db.execute(
            """
            SELECT COALESCE(SUM(text_generations_count), 0) + COALESCE(SUM(image_generations_count), 0)
            FROM user_usage
            """
        )
        revenue_cursor = await db.execute(
            """
            SELECT COALESCE(SUM(amount), 0)
            FROM payments
            WHERE status = 'succeeded'
            """
        )

        users_count = (await users_count_cursor.fetchone())[0]
        active_subscriptions = (await active_subs_cursor.fetchone())[0]
        total_generations = (await generations_cursor.fetchone())[0]
        total_revenue = (await revenue_cursor.fetchone())[0]

    return {
        "users_count": users_count,
        "active_subscriptions": active_subscriptions,
        "total_generations": total_generations,
        "total_revenue": float(total_revenue),
    }


async def save_or_update_payment(
    db_path: str, payment_id: str, user_id: int, amount: float, status: str
) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO payments (payment_id, user_id, amount, status)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(payment_id) DO UPDATE SET
                status = excluded.status,
                updated_at = CURRENT_TIMESTAMP
            """,
            (payment_id, user_id, amount, status),
        )
        await db.commit()


async def save_generated_post(
    db_path: str,
    user_id: int,
    generation_type: str,
    prompt: str,
    result: str | None,
    generation_succeeded: bool,
    error_message: str | None = None,
) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO generated_posts (
                user_id,
                generation_type,
                prompt,
                result,
                generation_succeeded,
                error_message
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                generation_type,
                prompt,
                result,
                generation_succeeded,
                error_message,
            ),
        )
        await db.commit()
