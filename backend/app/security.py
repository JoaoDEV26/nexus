"""Senhas com Argon2; JWT curto; refresh opaco e rotativo."""

import hashlib
import os
import secrets
import time
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session
from .db import get_db
from .models import RefreshSession, User, uid

SECRET = os.environ.get("JWT_SECRET", "")
if len(SECRET) < 32:
    raise RuntimeError("Defina JWT_SECRET com pelo menos 32 caracteres aleatórios.")
ORIGIN = os.environ.get("APP_ORIGIN", "http://localhost:5173").rstrip("/")
SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"
passwords = PasswordHash.recommended()
DUMMY_HASH = passwords.hash("dummy-password-for-timing")
bearer = HTTPBearer(auto_error=False)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def check_origin(request: Request):
    if request.headers.get("origin") != ORIGIN:
        raise HTTPException(403, "Origem não permitida")


def issue(db, user_id, response, family=None):
    raw = secrets.token_urlsafe(48)
    row = RefreshSession(
        user_id=user_id,
        token_hash=digest(raw),
        family_id=family or uid(),
        expires_at=int(time.time()) + 604800,
    )
    db.add(row)
    db.flush()
    response.set_cookie(
        "nexus_refresh",
        raw,
        httponly=True,
        secure=SECURE,
        samesite="strict",
        path="/api/v1/auth",
        max_age=604800,
    )
    token = jwt.encode(
        {
            "sub": user_id,
            "sid": row.id,
            "exp": int(time.time()) + 900,
            "iat": int(time.time()),
            "iss": "nexus",
            "aud": "nexus-web",
        },
        SECRET,
        algorithm="HS256",
    )
    return {"access_token": token, "token_type": "bearer"}


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)
):
    try:
        if not credentials:
            raise ValueError()
        payload = jwt.decode(
            credentials.credentials,
            SECRET,
            algorithms=["HS256"],
            issuer="nexus",
            audience="nexus-web",
            options={"require": ["sub", "sid", "exp", "iat"]},
        )
        session = db.get(RefreshSession, payload["sid"])
        if (
            not session
            or session.revoked
            or session.expires_at <= time.time()
            or session.user_id != payload["sub"]
        ):
            raise ValueError()
        user = db.get(User, payload["sub"])
        if not user:
            raise ValueError()
        return user
    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise HTTPException(401, "Sessão expirada ou inválida") from None


def refresh_session(db, request):
    raw = request.cookies.get("nexus_refresh", "")
    return db.scalar(select(RefreshSession).where(RefreshSession.token_hash == digest(raw)).with_for_update())
