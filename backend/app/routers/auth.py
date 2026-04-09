from datetime import datetime, timedelta
import random

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select
from authlib.integrations.starlette_client import OAuth

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db import get_session
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

oauth = OAuth()
if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

# OTP_STORE removed in favor of User model fields


@router.post("/register")
def register(email: str, password: str, full_name: str | None = None, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=email, full_name=full_name, hashed_password=get_password_hash(password))
    session.add(user)
    session.commit()
    session.refresh(user)
    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/login")
def login(email: str, password: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == email)).first()
    if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/otp/start")
def start_otp(phone: str, session: Session = Depends(get_session)):
    otp = str(random.randint(100000, 999999))
    user = session.exec(select(User).where(User.phone == phone)).first()
    if not user:
        user = User(phone=phone)
        session.add(user)
    
    user.otp_code = otp
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=5)
    session.add(user)
    session.commit()
    # In a real app, send SMS here
    return {"sent": True, "otp_debug": otp}


@router.post("/otp/verify")
def verify_otp(phone: str, otp: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.phone == phone)).first()
    if not user or user.otp_code != otp:
        raise HTTPException(status_code=401, detail="Invalid OTP")
    
    if user.otp_expires_at and user.otp_expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="OTP expired")
    
    # Clear OTP after verification
    user.otp_code = None
    user.otp_expires_at = None
    session.add(user)
    session.commit()
    
    token = create_access_token(str(user.id), timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES or 60))
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.get("/google/login")
async def google_login(request: Request):
    if "google" not in oauth:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, session: Session = Depends(get_session)):
    if "google" not in oauth:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    if not user_info:
        raise HTTPException(status_code=400, detail="Google userinfo missing")
    user = session.exec(select(User).where(User.email == user_info["email"])).first()
    if not user:
        user = User(email=user_info["email"], full_name=user_info.get("name"), oauth_provider="google", oauth_subject=user_info.get("sub"))
        session.add(user)
        session.commit()
        session.refresh(user)
    access = create_access_token(str(user.id))
    return {"access_token": access, "token_type": "bearer", "user": user}
