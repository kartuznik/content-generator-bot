from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from flask import Blueprint, current_app, render_template

from web.auth import requires_basic_auth


dashboard_bp = Blueprint("dashboard", __name__)


def _fetch_dashboard_stats(db_path: str) -> dict:
    now_iso = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        users_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        active_subscriptions = conn.execute(
            """
            SELECT COUNT(*)
            FROM user_usage
            WHERE is_subscribed = 1
              AND (subscription_expires_at IS NULL OR subscription_expires_at > ?)
            """,
            (now_iso,),
        ).fetchone()[0]
        total_generations = conn.execute(
            """
            SELECT COALESCE(SUM(text_generations_count), 0) + COALESCE(SUM(image_generations_count), 0)
            FROM user_usage
            """
        ).fetchone()[0]
        total_revenue = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0)
            FROM payments
            WHERE status = 'succeeded'
            """
        ).fetchone()[0]
    return {
        "users_count": users_count,
        "active_subscriptions": active_subscriptions,
        "total_generations": total_generations,
        "total_revenue": float(total_revenue or 0),
    }


@dashboard_bp.route("/")
@requires_basic_auth
def index():
    stats = _fetch_dashboard_stats(current_app.config["DB_PATH"])
    return render_template("dashboard.html", stats=stats)
