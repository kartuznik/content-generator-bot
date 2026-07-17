from __future__ import annotations

import hmac
from functools import wraps

from flask import current_app, redirect, request, session, url_for


SESSION_AUTH_KEY = "web_admin_authenticated"


def verify_password(raw_password: str) -> bool:
    expected_password = current_app.config.get("ADMIN_WEB_PASSWORD", "")
    return hmac.compare_digest(raw_password or "", expected_password or "")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get(SESSION_AUTH_KEY):
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def mark_logged_in() -> None:
    session[SESSION_AUTH_KEY] = True
    session.permanent = True


def logout_user() -> None:
    session.pop(SESSION_AUTH_KEY, None)


def is_login_request() -> bool:
    return request.path.startswith("/login")
