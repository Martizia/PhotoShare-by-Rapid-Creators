import re
import time
from ipaddress import ip_address
from typing import Callable

from fastapi import Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

BANNED_IPS = [ip_address("192.168.1.1"), ip_address("192.168.1.2"), ip_address("127.0.0.1")]
ALLOWED_IPS = [ip_address('192.168.1.0'), ip_address('172.16.0.0'), ip_address("127.0.0.1")]
USER_AGENT_BAN = [r"Gecko", r"Python-urllib"]


class CustomHeaderMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super(CustomHeaderMiddleware, self).__init__(app)

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        response.headers['Custom'] = 'Example'

        return response


class BlackListMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable):
        ip = ip_address(request.client.host)
        if ip in BANNED_IPS:
            return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "You are banned"})
        response = await call_next(request)
        return response


class WhiteListMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable):
        ip = ip_address(request.client.host)
        if ip not in ALLOWED_IPS:
            return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "Not allowed IP address"})
        response = await call_next(request)
        return response


class UserAgentBanMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable):
        print(f"Request.headers: {request.headers}")
        user_agent = request.headers.get("user-agent")
        print(f"User Agent: {user_agent}")
        for ban_pattern in USER_AGENT_BAN:
            if re.search(ban_pattern, user_agent):
                return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "You are banned"})
        response = await call_next(request)
        return response


class CustomCORSMiddleware(CORSMiddleware):
    def __init__(self, app, origins=None, allow_credentials=True, allow_methods=None, allow_headers=None):
        super().__init__(
            app,
            allow_origins=origins or ["*"],
            allow_credentials=allow_credentials,
            allow_methods=allow_methods,
            allow_headers=allow_headers
        )
