from enum import Enum

from api.core.logger import logger


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
    logger.debug(f"Checking access for user role '{user_role}' to required role '{required_role}'")

    if user_role not in ROLE_HIERARCHY:
        logger.debug(f"User role '{user_role}' is not a valid role")
        return False

    has_access = required_role in ROLE_HIERARCHY[user_role]

    if has_access:
        pass
        logger.debug(f"User role '{user_role}' has access to required role '{required_role}'")
    else:
        logger.debug(f"User role '{user_role}' does NOT have access to required role '{required_role}'")

    return has_access
