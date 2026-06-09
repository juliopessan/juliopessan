from fastapi import Request
from fastapi.responses import RedirectResponse
from config.settings import ADMIN_PASSWORD, SECRET_KEY
from itsdangerous import URLSafeSerializer

_serializer = URLSafeSerializer(SECRET_KEY, salt="admin-session")
COOKIE_NAME = "admin_session"


def create_session_token() -> str:
    return _serializer.dumps({"authenticated": True})


def verify_session(request: Request) -> bool:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return False
    try:
        data = _serializer.loads(token)
        return data.get("authenticated") is True
    except Exception:
        return False


def check_password(password: str) -> bool:
    return password == ADMIN_PASSWORD


def require_auth(request: Request):
    if not verify_session(request):
        return RedirectResponse("/admin/login", status_code=302)
    return None
