from __future__ import annotations

import sqlite3

from flask import Blueprint, current_app, redirect, render_template, request, url_for

from web.auth import login_required


users_bp = Blueprint("users", __name__, url_prefix="/users")


def _list_users(db_path: str) -> list[dict]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT
                u.user_id,
                u.username,
                COALESCE(uu.free_generations_left, 3) AS free_generations_left,
                COALESCE(uu.is_subscribed, 0) AS is_subscribed,
                uu.subscription_expires_at
            FROM users AS u
            LEFT JOIN user_usage AS uu ON uu.user_id = u.user_id
            ORDER BY u.created_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


@users_bp.get("/")
@login_required
def users_page():
    users = _list_users(current_app.config["DB_PATH"])
    return render_template("users.html", users=users)


@users_bp.post("/topup")
@login_required
def topup_generations():
    db_path = current_app.config["DB_PATH"]
    user_id = int(request.form.get("user_id", "0"))
    topup_amount = 5

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO user_usage (user_id, free_generations_left)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                free_generations_left = user_usage.free_generations_left + excluded.free_generations_left,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, topup_amount),
        )
        conn.commit()

    return redirect(url_for("users.users_page"))
