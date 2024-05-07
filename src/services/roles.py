from fastapi import Depends, HTTPException, Request, status

from src.database.models import Role, User
from src.services.auth import auth_service


class RoleAccess:
    """
    Class for checking user role access
    """
    def __init__(self, allowed_roles: list[Role]):
        self.allowed_roles = allowed_roles

    async def __call__(self, request: Request, user: User = Depends(auth_service.get_current_user)):
        """
        Check user role access

        :param request: Request base url
        :type request: Request
        :param user: Current user object from auth service
        :type user: User
        :return: None
        :rtype: None
        """
        print(user.role, self.allowed_roles)

        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access Forbidden"
            )