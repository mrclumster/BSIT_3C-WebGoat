import re
import bcrypt

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")

def hash_password(plain: str) -> bytes:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12))

def verify_password(plain: str, hashed: bytes) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed)
    except (ValueError, TypeError):
        return False

def validate_username(username: str) -> str | None:
    if not username:
        return "Username is required."
    if not USERNAME_RE.match(username):
        return "Username must be 3-32 chars: letters, digits, '.', '_', '-'."
    return None

def validate_password(password: str) -> str | None:
    if not password or len(password) < 8:
        return "Password must be at least 8 characters."
    if len(password) > 128:
        return "Password is too long."
    return None
