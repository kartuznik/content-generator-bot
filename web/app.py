from __future__ import annotations

import asyncio

from flask import Flask, jsonify, render_template, request

from bot.config import load_settings
from bot.database import init_db
from bot.handlers.payment import process_yookassa_webhook
from bot.services.yookassa_client import YooKassaClient
from web.routes.dashboard import dashboard_bp
from web.routes.users import users_bp


def create_app() -> Flask:
    settings = load_settings()
    asyncio.run(init_db(settings.db_path))

    app = Flask(__name__, template_folder="templates")
    app.config["DB_PATH"] = settings.db_path
    app.config["ADMIN_WEB_PASSWORD"] = settings.admin_web_password

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(users_bp)

    @app.get("/login")
    def login_help():
        return render_template("login.html")

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
