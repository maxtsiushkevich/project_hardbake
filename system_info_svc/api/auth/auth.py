from fastapi import Request, HTTPException, status, Depends
from jose import jwt, JWTError
from pydantic import BaseModel
from enum import Enum
from typing import Callable

from api.core.logger import logger

with open("public_key.pem", "r") as f:
    logger.info("Read public key")
    PUBLIC_KEY = f.read()


class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


ROLE_HIERARCHY = {
    Role.ADMIN: [Role.ADMIN, Role.USER, Role.VIEWER],
    Role.USER: [Role.USER, Role.VIEWER],
    Role.VIEWER: [Role.VIEWER]
}


def has_role_access(user_role: Role, required_role: Role) -> bool:
    return required_role in ROLE_HIERARCHY.get(user_role, [])


class TokenUser(BaseModel):
    id: int
    username: str
    role: Role
    is_active: bool


def get_current_user(
        request: Request,
) -> TokenUser:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=["ES256"])
        user = TokenUser(
            id=int(payload.get("sub")),
            username=payload.get("username"),
            role=Role(payload.get("role")),
            is_active=payload.get("is_active"),
        )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is inactive"
            )

        return user

    except (JWTError, ValueError, KeyError) as e:
        print(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def require_role(role: Role) -> Callable:
    def role_dependency(current_user: TokenUser = Depends(get_current_user)):
        if not has_role_access(current_user.role, role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return role_dependency
