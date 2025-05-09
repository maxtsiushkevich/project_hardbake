from typing import List

from fastapi import Depends, HTTPException, status, Request, APIRouter, Response, Query
from sqlalchemy.orm import Session
from jose import jwt

from api.core.auth import config, auth
from api.core.logger import logger
from api.core.roles import Role, has_role_access
from api.services.users import create_user, get_user, delete_user_by_username, get_users_paginated
from api.utils.database import get_db
from api.schemas.schemas import UserCreate, User as UserSchema
from api.models.models import User

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        logger.warning("No access token found in request cookies")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = jwt.decode(token, config.JWT_PUBLIC_KEY, algorithms=[config.JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User with ID {user_id} not found.")
            raise HTTPException(status_code=404, detail="User not found")
        logger.debug(f"User {user.username} authenticated successfully.")
        return user
    except Exception as e:
        logger.error(f"Error decoding token: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


def require_role(role: Role):
    def role_checker(current_user: User = Depends(get_current_user)):
        if not has_role_access(Role(current_user.role), role):
            logger.warning(f"User {current_user.username} does not have {role} access.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        logger.debug(f"User {current_user.username} has {role} access.")
        return current_user

    return role_checker


@router.post("/token",
             responses={
                 401: {"description": "Unauthorized"},
             }
             )
async def login_for_access_token(
        response: Response,
        username: str,
        password: str,
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.verify_password(password):
        logger.warning(f"Failed login attempt for username: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    logger.debug(f"User {username} successfully authenticated.")
    token = auth.create_access_token(uid=str(user.id), role=user.role, data={
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "is_active": user.is_active,
    })
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax"
    )
    logger.debug(f"Access token set for user {username}.")
    return {"access_token": token}


@router.post("/users/", response_model=UserSchema,
             responses={
                 401: {"description": "Unauthorized"},
                 403: {"description": "Forbidden"},
             }
             )
def create_new_user(
        user: UserCreate,
        current_user: User = Depends(require_role(Role.ADMIN)),
        db: Session = Depends(get_db)
):
    logger.debug(f"Admin user {current_user.username} is creating a new user {user.username}.")
    db_user = get_user(db, username=user.username)
    if db_user:
        logger.warning(f"Username {user.username} already registered.")
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = create_user(db=db, user=user)
    logger.debug(f"User {new_user.username} created successfully.")
    return new_user


@router.get("/users/me/", response_model=UserSchema,
            responses={
                401: {"description": "Unauthorized"},
            }
            )
async def read_my_profile(current_user: User = Depends(get_current_user)):
    logger.debug(f"Fetching current user {current_user.username}.")
    return current_user


@router.delete("/users/{username}",
               responses={
                   401: {"description": "Unauthorized"},
                   403: {"description": "Forbidden"},
                   404: {"description": "User not found"},
               })
def delete_user(
        username: str,
        current_user: User = Depends(require_role(Role.ADMIN)),
        db: Session = Depends(get_db)
):
    logger.debug(f"Admin user {current_user.username} attempts to delete user {username}.")
    success = delete_user_by_username(db, username=username)
    if not success:
        logger.warning(f"User {username} not found for deletion.")
        raise HTTPException(status_code=404, detail="User not found")
    logger.debug(f"User {username} successfully deleted.")
    return {"message": f"User '{username}' deleted successfully"}


@router.get("/users/", response_model=List[UserSchema],
            responses={
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden"},
            })
def list_users(
        start_pos: int = Query(0, ge=0),
        quantity: int = Query(10, gt=0),
        current_user: User = Depends(require_role(Role.ADMIN)),
        db: Session = Depends(get_db)
):
    logger.debug(f"Admin user {current_user.username} requests user list from {start_pos} with quantity {quantity}.")
    users = get_users_paginated(db, start_pos=start_pos, quantity=quantity)
    return users


# @router.get("/admin/",
#             responses={
#                 401: {"description": "Unauthorized"},
#                 403: {"description": "Forbidden"},
#             }
#             )
# async def admin_demo_route(current_user: User = Depends(require_role(Role.ADMIN))):
#     logger.debug(f"User {current_user.username} has admin access.")
#     return {"message": "Admin access granted"}
#
#
# @router.get("/user/",
#             responses={
#                 401: {"description": "Unauthorized"},
#                 403: {"description": "Forbidden"},
#             }
#             )
# async def user_demo_route(current_user: User = Depends(require_role(Role.USER))):
#     logger.debug(f"User {current_user.username} has user access.")
#     return {"message": "User access granted"}
#
#
# @router.get("/viewer/",
#             responses={
#                 401: {"description": "Unauthorized"},
#                 403: {"description": "Forbidden"},
#             }
#             )
# async def viewer_demo_route(current_user: User = Depends(require_role(Role.VIEWER))):
#     logger.debug(f"User {current_user.username} has viewer access.")
#     return {"message": "Viewer access granted"}


@router.post("/logout")
async def logout(response: Response):
    logger.debug("Logging out user and deleting access token.")
    response.delete_cookie("access_token")
    return {"message": "Successfully logged out"}