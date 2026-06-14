from datetime import datetime, timedelta
import random

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlmodel import Session, select
from authlib.integrations.starlette_client import OAuth
import httpx

from app.core.config import settings
from app.core.deps import get_current_user
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


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register")
def register(req: RegisterRequest, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.email == req.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=req.email, full_name=req.full_name, hashed_password=get_password_hash(req.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/login")
def login(req: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == req.email)).first()
    if not user or not user.hashed_password or not verify_password(req.password, user.hashed_password):
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
    response: dict = {"sent": True}
    if settings.DEBUG:
        response["otp_debug"] = otp  # Only expose OTP in debug/dev mode
    return response


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


class GoogleLoginRequest(BaseModel):
    token: str

@router.post("/google")
def google_login_spa(req: GoogleLoginRequest, session: Session = Depends(get_session)):
    resp = httpx.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {req.token}"}
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Invalid Google token")
    user_info = resp.json()
        
    email = user_info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email not provided by Google")
        
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        user = User(
            email=email,
            full_name=user_info.get("name"),
            oauth_provider="google",
            oauth_subject=user_info.get("sub")
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
    access = create_access_token(str(user.id))
    return {"access_token": access, "token_type": "bearer", "user": user}


@router.post("/token")
def oauth2_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    """OAuth2 password flow token endpoint used by the frontend."""
    user = session.exec(select(User).where(User.email == form_data.username)).first()
    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    """Return current authenticated user profile."""
    return {
        "id": user.id,
        "email": user.email,
        "phone": user.phone,
        "full_name": user.full_name,
        "is_admin": user.is_admin,
        "genre_preferences": user.genre_preferences,
        "created_at": user.created_at,
    }
