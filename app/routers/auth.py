from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import current_user_id, db_session
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.refresh import RefreshTokenStore

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_token_pair(user_id: int) -> TokenResponse:
    refresh_token, jti = create_refresh_token(user_id)
    RefreshTokenStore().store(jti, user_id)
    return TokenResponse(
        access_token=create_access_token(user_id), refresh_token=refresh_token
    )


@router.post("/register", response_model=UserResponse, status_code=201)
def register(p: RegisterRequest, db: Session = Depends(db_session)):
    email = p.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Email already registered")
    u = User(email=email, password_hash=hash_password(p.password))
    db.add(u)
    db.commit()
    db.refresh(u)
    return UserResponse(id=u.id, email=u.email, created_at=u.created_at.isoformat())


@router.post("/login", response_model=TokenResponse)
def login(p: LoginRequest, db: Session = Depends(db_session)):
    u = db.scalar(select(User).where(User.email == p.email.lower()))
    if not u or not verify_password(p.password, u.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return _issue_token_pair(u.id)


@router.post("/refresh", response_model=TokenResponse)
def refresh(p: RefreshRequest):
    """Rotate a refresh token: the old one is revoked, a new pair is issued."""
    try:
        user_id, jti = decode_refresh_token(p.refresh_token)
    except ValueError:
        raise HTTPException(401, "Invalid refresh token")
    store = RefreshTokenStore()
    if not store.is_valid(jti, user_id):
        raise HTTPException(401, "Refresh token revoked or expired")
    store.revoke(jti)
    return _issue_token_pair(user_id)


@router.post("/logout", status_code=204)
def logout(p: RefreshRequest):
    """Revoke a refresh token immediately."""
    try:
        _, jti = decode_refresh_token(p.refresh_token)
    except ValueError:
        raise HTTPException(401, "Invalid refresh token")
    RefreshTokenStore().revoke(jti)
    return None


@router.get("/me", response_model=UserResponse)
def me(uid=Depends(current_user_id), db: Session = Depends(db_session)):
    u = db.get(User, uid)
    if not u:
        raise HTTPException(404, "User not found")
    return UserResponse(id=u.id, email=u.email, created_at=u.created_at.isoformat())
