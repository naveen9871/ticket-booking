from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from sqlmodel import Session, select

from app.core.config import settings
from app.db import get_session
from app.models import User


ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    user_id = int(payload.get("sub"))
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_optional_user(token: str | None = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User | None:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    return session.exec(select(User).where(User.id == int(user_id))).first()
