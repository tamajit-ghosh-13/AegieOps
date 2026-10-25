"""FastAPI router for authentication and team management APIs (AegisOps Slice 6)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from auth.dependencies import get_current_user, require_role
from auth.models import LoginRequest, Role, Token, User
from auth.security import DEFAULT_EXPIRE_MINUTES, create_access_token
from auth.service import AuthService, get_auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(
    req: LoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    """Authenticate with email and password to receive JWT access token."""
    user = service.authenticate(req.email, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token_data = {
        "sub": user.id,
        "email": user.email,
        "role": user.role.value,
        "team_id": user.team_id,
    }
    token = create_access_token(token_data)

    # Set auth cookie for seamless browser/UI navigation
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=DEFAULT_EXPIRE_MINUTES * 60,
        samesite="lax",
    )

    return Token(
        access_token=token,
        token_type="bearer",
        expires_in=DEFAULT_EXPIRE_MINUTES * 60,
        user=user,
    )


@router.get("/me", response_model=User)
async def get_me(user: User = Depends(get_current_user)):
    """Retrieve profile of the currently logged-in user."""
    return user


@router.get("/users", response_model=list[User])
async def list_team_users(
    user: User = Depends(require_role(Role.admin, Role.responder)),
    service: AuthService = Depends(get_auth_service),
):
    """List members belonging to the operator's team."""
    return service.list_users(team_id=user.team_id)
