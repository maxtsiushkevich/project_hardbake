from typing import Type

from sqlalchemy.orm import Session

from api.core.logger import logger
from api.models.models import User, pwd_context
from api.schemas.schemas import UserCreate


def get_user(db: Session, username: str):
    logger.debug(f"Fetching user with username: {username}")
    user = db.query(User).filter(User.username == username).first()
    if user:
        logger.debug(f"User found: {user.username}")
    else:
        logger.warning(f"User with username {username} not found")
    return user


def create_user(db: Session, user: UserCreate):
    logger.debug(f"Creating a new user with username: {user.username}")

    hashed_password = pwd_context.hash(user.password)
    logger.debug(f"Password for user {user.username} hashed successfully")

    db_user = User(
        username=user.username,
        hashed_password=hashed_password,
        role=user.role
    )

    logger.debug(f"Adding user {user.username} to the database")
    db.add(db_user)

    try:
        db.commit()
        db.refresh(db_user)
        logger.debug(f"User {user.username} created and committed to the database successfully")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user {user.username}: {e}")
        raise

    return db_user


def delete_user_by_username(db: Session, username: str) -> bool:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True


def get_users_paginated(db: Session, start_pos: int, quantity: int) -> list[Type[User]]:
    return db.query(User).offset(start_pos).limit(quantity).all()
