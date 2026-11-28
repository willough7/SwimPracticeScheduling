"""Admin login sessions and the check that protects create/edit routes.

How a login works:
1. The admin sends their username and password to POST /auth/login.
2. If they're right, the server makes a long random token, remembers it, and
   sends it back in a cookie. The browser then includes that cookie with every
   request to this site automatically.
3. Routes that change data depend on require_admin, which looks the cookie's
   token up. No valid token means 401, whatever the frontend shows or hides.

The cookie is:
- HttpOnly: page JavaScript can't read it, so a script injected into the
  page can't steal the login.
- Secure: only sent over HTTPS (browsers treat http://localhost as secure, so
  this still works in development).
- SameSite=Strict: never sent on requests that come from another website, so
  a malicious page can't make the admin's browser change data behind their back.

Sessions are kept in memory, so restarting the server logs everyone out. The
server only stores a hash of each token, so even someone who could read the
server's memory couldn't copy an admin's cookie from it.
"""

import hashlib
import os
import secrets
import time

from fastapi import Cookie, Depends, HTTPException, Response

SESSION_COOKIE = "admin_session"
SESSION_SECONDS = 12 * 60 * 60          # a login lasts 12 hours
# Set COOKIE_SECURE=false only if you ever test over plain http on another
# machine; never in production.
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "true").lower() != "false"

# sha256(token) -> (username, expires_at)
sessions: dict[str, tuple[str, float]] = {}


def _token_key(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def start_session(response: Response, username: str) -> None:
    token = secrets.token_urlsafe(32)   # 256 random bits: can't be guessed
    sessions[_token_key(token)] = (username, time.time() + SESSION_SECONDS)
    response.set_cookie(SESSION_COOKIE, token, max_age=SESSION_SECONDS, path="/",
                        httponly=True, secure=COOKIE_SECURE, samesite="strict")


def end_session(response: Response, token: str | None) -> None:
    if (token is not None):
        sessions.pop(_token_key(token), None)
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True,
                           secure=COOKIE_SECURE, samesite="strict")


def current_admin(admin_session: str | None = Cookie(default=None)) -> str | None:
    """The logged-in admin's username, or None for everyone else."""
    if (admin_session is None):
        return None
    key = _token_key(admin_session)
    entry = sessions.get(key)
    if (entry is None):
        return None
    username, expires_at = entry
    if (time.time() > expires_at):
        sessions.pop(key, None)
        return None
    return username


def require_admin(admin: str | None = Depends(current_admin)) -> str:
    """Add to any route only admins may use: dependencies=[Depends(require_admin)]."""
    if (admin is None):
        raise HTTPException(status_code=401, detail="Admin login required")
    return admin
