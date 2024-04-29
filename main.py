from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis
from middlewares import (BlackListMiddleware, CustomCORSMiddleware,
                         CustomHeaderMiddleware, UserAgentBanMiddleware,
                         WhiteListMiddleware)
from src.database.db import get_db
from src.config.config import config
from src.routes import comments, auth, users, images, rating

import uvicorn

app = FastAPI()

origins = ["*"]
app.add_middleware(CustomHeaderMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix='/api')
app.include_router(users.router, prefix='/api')
# app.include_router(images.router, prefix='/api')
# app.include_router(comments.router, prefix='/api')
app.include_router(rating.router, prefix='/api')

BASE_DIR = Path(".")

app.mount("/static", StaticFiles(directory=BASE_DIR / "src" / "static"), name="static")


@app.on_event("startup")
async def startup():
    r = await redis.Redis(host=config.REDIS_DOMAIN, port=config.REDIS_PORT, db=0,
                          password=config.REDIS_PASSWORD, encoding="utf-8",
                          decode_responses=True)
    await FastAPILimiter.init(r)
templates = Jinja2Templates(directory=BASE_DIR / "src" / "templates")  # noqa

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "target": "Go IT Students"})


@app.get('/api/healthchecker')
async def healthchecker(db: AsyncSession = Depends(get_db)):
    """
    This function checks the health of the database connection by executing a test query.

    :param db: An async database connection.
    :type db: AsyncSession
    :return: A dictionary with a message indicating the health status of the database connection.
    :raises HTTPException 500: If there is an error connecting to the database or the database is not configured correctly.

    """
    try:
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail="Database is not configured correctly")
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
