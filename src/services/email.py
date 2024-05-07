from pathlib import Path
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.config.config import config
from src.services.auth import auth_service


conf = ConnectionConfig(
    MAIL_USERNAME=config.MAIL_USERNAME,
    MAIL_PASSWORD=config.MAIL_PASSWORD,
    MAIL_FROM=config.MAIL_FROM,
    MAIL_PORT=config.MAIL_PORT,
    MAIL_SERVER=config.MAIL_SERVER,
    MAIL_FROM_NAME="Photo Share Admin",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / 'templates',
)

async def send_email(email: EmailStr, username: str, host: str):
    """
    Send email verification to user with token

    :param email: email of user
    :type email: EmailStr
    :param username: username of user
    :type username: str
    :param host: base url
    :type host: str
    :return: None
    :rtype: None
    """
    try:
        token_verification = auth_service.create_email_token({"sub": email})
        message = MessageSchema(
            subject="Confirm your email ",
            recipients=[email],
            template_body={"host": host, "username": username, "token": token_verification},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="email_verification.html")
    except ConnectionErrors as err:
        print(err)
        raise err


async def send_password_reset_email(email: EmailStr, username: str, reset_token: str, host: str):
    """
    Send password reset link to user's email address

    :param email: Email address of user
    :type email: EmailStr
    :param username: Username of user
    :type username: str
    :param reset_token: Password reset token
    :type reset_token: str
    :param host: Base url
    :type host: str
    :return: None
    :rtype: None
    """
    try:
        message = MessageSchema(
            subject="Password Reset",
            recipients=[email],
            template_body={"host": host, "username": username, "reset_token": reset_token},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="password_reset_email.html")
    except ConnectionErrors as err:
        print(err)
        raise err
