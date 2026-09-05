"""Cookie-based authentication helper."""

import hashlib
from fastapi import Request, HTTPException
from api.database import SessionLocal
from api.models import User


SECRET_KEY = "ansible-dynamic-inventory-secret-key"


def hash_password(password: str) -> str:
    return hashlib.sha256((password + SECRET_KEY).encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def get_current_user(request: Request) -> User:
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=303, headers={"Location": "/login"})

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == session_id).first()
        if not user:
            raise HTTPException(status_code=303, headers={"Location": "/login"})
        return user
    finally:
        db.close()
