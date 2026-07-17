from __future__ import annotations

import sqlite3

from flask import Blueprint, current_app, render_template

from web.auth import login_required


generations_bp = Blueprint("generations", __name__, url_prefix="/generations")


def _fetch_recent_generations(db_path: str) -> list[dict]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT
                id,
                user_id,
                generation_type,
                prompt,
                generation_succeeded,
                created_at
            FROM generated_posts
            ORDER BY id DESC
            LIMIT 50
            """
        ).fetchall()
    return [dict(row) for row in rows]


@generations_bp.get("/")
@login_required
def generations_page():
    generations = _fetch_recent_generations(current_app.config["DB_PATH"])
    return render_template("generations.html", generations=generations)
