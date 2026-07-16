from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

from flask import Blueprint, current_app, redirect, render_template, request, url_for

from web.auth import requires_basic_auth


users_bp = Blueprint("users", __name__, url_prefix="/users")


def _list_users(db_path: str) -> list[dict]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT
                u.user_id,
                u.username,
                u.first_name,
                COALESCE(uu.text_generations_count, 0) AS text_generations_count,
                COALESCE(uu.image_generations_count, 0) AS image_generations_count,
                COALESCE(uu.free_generations_left, 3) AS free_generations_left,
                uu.subscription_expires_at,
                COALESCE(uu.is_subscribed, 0) AS is_subscribed
            FROM users u
            LEFT JOIN user_usage uu ON uu.user_id = u.user_id
            ORDER BY u.created_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


@users_bp.route("/", methods=["GET"])
@requires_basic_auth
def users_page():
    users = _list_users(current_app.config["DB_PATH"])
    return render_template("users.html", users=users)


@users_bp.route("/add-generations", methods=["POST"])
@requires_basic_auth
def add_generations():
    db_path = current_app.config["DB_PATH"]
    user_id = int(request.form.get("user_id", "0"))
    amount = max(int(request.form.get("amount", "0")), 0)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO user_usage (user_id, free_generations_left)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                free_generations_left = free_generations_left + excluded.free_generations_left,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, amount),
        )
        conn.commit()
    return redirect(url_for("users.users_page"))


@users_bp.route("/extend-subscription", methods=["POST"])
@requires_basic_auth
def extend_subscription():
    db_path = current_app.config["DB_PATH"]
    user_id = int(request.form.get("user_id", "0"))
    days = max(int(request.form.get("days", "30")), 1)

    now = datetime.now(timezone.utc)
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT subscription_expires_at FROM user_usage WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if row and row[0]:
            try:
                current_expiry = datetime.fromisoformat(row[0])
            except ValueError:
                current_expiry = now
            start = current_expiry if current_expiry > now else now
        else:
            start = now
        new_expiry = start + timedelta(days=days)

        conn.execute(
            """
            INSERT INTO user_usage (user_id, is_subscribed, subscription_expires_at)
            VALUES (?, 1, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                is_subscribed = 1,
                subscription_expires_at = excluded.subscription_expires_at,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, new_expiry.isoformat()),
        )
        conn.commit()
    return redirect(url_for("users.users_page"))
