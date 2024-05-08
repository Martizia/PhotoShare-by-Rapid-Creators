from fastapi import (APIRouter, BackgroundTasks, Depends, HTTPException,
                     Request, status)

from fastapi.security import (HTTPAuthorizationCredentials, HTTPBearer,
                              OAuth2PasswordRequestForm)
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.db import get_db
from src.database.models import Role, User
from src.repository import users as repository_users
from src.services.roles import RoleAccess
from fastapi.responses import JSONResponse
from src.schemas.users import RequestEmail, TokenModel, UserModel, UserResponse, PasswordResetRequest, PasswordReset
from src.services.auth import auth_service, add_blacklist_token
from src.services.email import send_email, send_password_reset_email

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Could not validate credentials',
    headers={'WWW-Authenticate': 'Bearer'},
)

router = APIRouter(prefix='/auth', tags=["Authorization"])
get_refresh_token = HTTPBearer()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserModel, background_tasks: BackgroundTasks, request: Request,
                 db: AsyncSession = Depends(get_db)):
    """
    Create new user

    :param body: The data for the new user
    :type body: UserModel
    :param background_tasks: Background tasks
    :type background_tasks: BackgroundTasks
    :param request: Request base url
    :type request: Request
    :param db: The async database session
    :type db: AsyncSession
    :return: The created user
    :rtype: User
    """
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    background_tasks.add_task(send_email, new_user.email, new_user.username, str(request.base_url))
    return new_user


@router.post("/login", response_model=TokenModel, status_code=status.HTTP_200_OK)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    Login user

    :param body: The data for the login
    :type body: OAuth2PasswordRequestForm
    :param db: The async database session
    :type db: AsyncSession
    :return: The access and refresh tokens
    :rtype: TokenModel
    """
    user = await repository_users.get_user_by_email(body.username, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email address")
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed")
    if user.banned:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is banned")
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/logout')
def logout(token: str = Depends(auth_service.get_current_user_token)):
    """
    Logout user

    :param token: The access token
    :type token: str
    :return: The result of the logout
    :rtype: JSONResponse
    """
    if add_blacklist_token(token):
        return JSONResponse({'result': True})
    raise CREDENTIALS_EXCEPTION


@router.get('/refresh_token', response_model=TokenModel)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(get_refresh_token),
                        db: AsyncSession = Depends(get_db),
                        current_user: User = Depends(auth_service.get_current_user)):
    """
    Refreshes access token

    :param credentials: Credentials for the refresh token
    :type credentials: HTTPAuthorizationCredentials
    :param db: The async database session
    :type db: AsyncSession
    :param current_user: The current user
    :type current_user: User
    :return: The access and refresh tokens
    :rtype: Token
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str,
                          db: AsyncSession = Depends(get_db)):
    """
    Confirms email address for user with given token

    :param token: Token for email confirmation
    :type token: str
    :param db: The async database session
    :type db: AsyncSession
    :return: The result of the email confirmation
    :rtype: JSONResponse
    """
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repository_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post('/request_email', dependencies=[Depends(RateLimiter(times=1, seconds=10))],
             description="No more than 1 request per 10 second")
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: AsyncSession = Depends(get_db)):
    """
    Requests email confirmation for user with given email address

    :param body: Email address for email confirmation
    :type body: RequestEmail
    :param background_tasks: Background tasks for sending email
    :type background_tasks: BackgroundTasks
    :param request: Request base url
    :type request: Request
    :param db: The async database session
    :type db: AsyncSession
    :return: The result of the email request
    :rtype: JSONResponse
    """
    user = await repository_users.get_user_by_email(body.email, db)
    if user:
        if user.confirmed:
            return {"message": "Your email is already confirmed"}
        else:
            background_tasks.add_task(send_email, user.email, user.username, str(request.base_url))
            return {"message": "Check your email for confirmation."}
    else:
        return {"message": "User with this email does not exist."}


@router.post("/forgot_password", dependencies=[Depends(RateLimiter(times=1, seconds=10))],
             description="No more than 1 request per 10 second")
async def forgot_password(body: PasswordResetRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Sends password reset link to user's email address

    :param body: Email address for password reset
    :type body: PasswordResetRequest
    :param request: Request base url
    :type request: Request
    :param db: The async database session
    :type db: AsyncSession
    :return: The result of the password reset
    :rtype: JSONResponse
    """
    user = await repository_users.get_user_by_email(body.email, db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    reset_token = auth_service.create_email_token({"sub": body.email})
    await send_password_reset_email(user.email, user.username, reset_token, str(request.base_url))

    await repository_users.store_reset_token(body.email, reset_token, db)

    return {"message": "Reset password link sent to your email"}


@router.post("/reset_password/{token}")
async def reset_password(body: PasswordReset, db: AsyncSession = Depends(get_db)):
    """
    Resets password for user with given token

    :param token: Token for password reset
    :type token: str
    :param body: New password for user
    :type body: PasswordReset
    :param db: The async database session
    :type db: AsyncSession
    :return: The result of the password reset
    :rtype: JSONResponse
    """
    email = await auth_service.get_email_from_token(body.token)
    user = await repository_users.get_user_by_email(email, db)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not await repository_users.verify_reset_token(email, body.token, db):
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    await repository_users.update_password(email, body.new_password, db)
    return {"message": "Password reset successfully"}


@router.put("/users/{email}/role", status_code=status.HTTP_200_OK)
async def change_user_role_by_email(
        email: str,
        new_role: Role,
        current_user: User = Depends(auth_service.get_current_user),
        session: AsyncSession = Depends(get_db),
):
    """
    Changes user role by email

    :param email: Email of the user to change role
    :type email: str
    :param new_role: New role for the user
    :type new_role: Role
    :param current_user: The current user
    :type current_user: User
    :param session: The async database session
    :type session: AsyncSession
    :return: The result of the role change
    :rtype: JSONResponse
    """
    role_access = RoleAccess([Role.admin])
    await role_access(request=None, user=current_user)
    user = await session.execute(select(User).where(User.email == email))
    user = user.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    user.role = new_role
    await session.commit()
    return {"message": "User role updated successfully"}


@router.put("/users/{email}/ban", status_code=status.HTTP_200_OK)
async def ban_user_by_email(
        email: str,
        current_user: User = Depends(auth_service.get_current_user),
        session: AsyncSession = Depends(get_db),
):
    """
    Bans user by email

    :param email: Email of the user to ban
    :type email: str
    :param current_user: The current user
    :type current_user: User
    :param session: The async database session
    :type session: AsyncSession
    :return: The result of the ban
    :rtype: JSONResponse
    """
    role_access = RoleAccess([Role.admin, Role.moderator])
    await role_access(request=None, user=current_user)
    user = await session.execute(select(User).where(User.email == email))
    user = user.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    user.banned = True
    await session.commit()
    return {"message": "User banned successfully"}


@router.put("/users/{email}/unban", status_code=status.HTTP_200_OK)
async def unban_user_by_email(
        email: str,
        current_user: User = Depends(auth_service.get_current_user),
        session: AsyncSession = Depends(get_db),
):
    """
    Unbans user by email

    :param email: Email of the user to unban
    :type email: str
    :param current_user: The current user
    :type current_user: User
    :param session: The async database session
    :type session: AsyncSession
    :return: The result of the unban
    :rtype: JSONResponse
    """
    role_access = RoleAccess([Role.admin, Role.moderator])

    await role_access(request=None, user=current_user)

    user = await session.execute(select(User).where(User.email == email))
    user = user.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.banned = False
    await session.commit()

    return {"message": "User unbanned successfully"}
