from __future__ import annotations

import sqlite3

from flask import Blueprint, current_app, render_template

from web.auth import login_required


dashboard_bp = Blueprint("dashboard", __name__)


def _fetch_dashboard_stats(db_path: str) -> dict:
    with sqlite3.connect(db_path) as conn:
        users_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        active_subscriptions = conn.execute(
            """
            SELECT COUNT(*)
            FROM user_usage
            WHERE COALESCE(is_subscribed, 0) = 1
            """
        ).fetchone()[0]
        successful_generations = conn.execute(
            """
            SELECT COUNT(*)
            FROM generated_posts
            WHERE generation_succeeded = 1
            """
        ).fetchone()[0]

    return {
        "users_count": int(users_count),
        "active_subscriptions": int(active_subscriptions),
        "successful_generations": int(successful_generations),
    }


@dashboard_bp.route("/")
@login_required
def index():
    stats = _fetch_dashboard_stats(current_app.config["DB_PATH"])
    return render_template("dashboard.html", stats=stats)
