from __future__ import annotations

from functools import wraps

from flask import Response, current_app, request


def _unauthorized() -> Response:
    return Response(
        "Authentication required",
        401,
        {"WWW-Authenticate": 'Basic realm="Content Generator Admin"'},
    )


def requires_basic_auth(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        auth = request.authorization
        expected_password = current_app.config.get("ADMIN_WEB_PASSWORD", "")
        if not auth or auth.username != "admin" or auth.password != expected_password:
            return _unauthorized()
        return view(*args, **kwargs)

    return wrapped
