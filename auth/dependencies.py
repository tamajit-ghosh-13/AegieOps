"""FastAPI dependencies for JWT authentication and RBAC validation (AegisOps Slice 6)."""

from __future__ import annotations

from typing import Annotated
from fastapi import Cookie, Depends, Header, HTTPException, Query, status

from auth.models import Role, User
from auth.security import decode_access_token
from auth.service import AuthService, get_auth_service


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    token_query: Annotated[str | None, Query(alias="token")] = None,
    access_token_cookie: Annotated[str | None, Cookie(alias="access_token")] = None,
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """Extract and validate bearer token from Header, Query, or Cookie."""
    token: str | None = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif token_query:
        token = token_query
    elif access_token_cookie:
        token = access_token_cookie

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = auth_service.get_user_by_id(payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_role(*allowed_roles: Role):
    """Enforce that the authenticated user possesses one of the allowed roles."""

    def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            role_names = [r.value for r in allowed_roles]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: role '{user.role.value}' is not authorized. Required: {role_names}",
            )
        return user

    return role_checker
