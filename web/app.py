from __future__ import annotations

import asyncio
import os

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for

from bot.config import Settings
from bot.database import init_db
from bot.handlers.payment import process_yookassa_webhook
from bot.services.yookassa_client import YooKassaClient
from web.auth import SESSION_AUTH_KEY, login_required, logout_user, mark_logged_in, verify_password
from web.routes.dashboard import dashboard_bp
from web.routes.generations import generations_bp
from web.routes.users import users_bp


def create_app() -> Flask:
    settings = Settings.from_env()
    asyncio.run(init_db(settings.db_path))

    app = Flask(__name__, template_folder="templates")
    app.config["DB_PATH"] = settings.db_path
    app.config["ADMIN_WEB_PASSWORD"] = settings.admin_web_password
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me-in-production")

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(generations_bp)

    @app.get("/login")
    def login():
        if session.get(SESSION_AUTH_KEY):
            return redirect(url_for("dashboard.index"))
        return render_template("login.html")

    @app.post("/login")
    def login_post():
        password = request.form.get("password", "")
        if verify_password(password):
            mark_logged_in()
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect(url_for("dashboard.index"))
        flash("Неверный пароль", "danger")
        return render_template("login.html"), 401

    @app.get("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    @app.post("/yookassa/webhook")
    def yookassa_webhook():
        payload = request.get_json(silent=True) or {}
        client = YooKassaClient(
            shop_id=settings.yokassa_shop_id,
            secret_key=settings.yokassa_secret_key,
            return_url=settings.yookassa_return_url,
            db_path=settings.db_path,
        )
        result = asyncio.run(process_yookassa_webhook(payload, client))
        return jsonify(result), 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
