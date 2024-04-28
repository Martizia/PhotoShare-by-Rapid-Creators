from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis

from src.database.db import get_db
from src.config.config import config
from src.routes import comments, auth, users, images, rating

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(auth.router, prefix='/api')
# app.include_router(users.router, prefix='/api')
# app.include_router(images.router, prefix='/api')
# app.include_router(comments.router, prefix='/api')
app.include_router(rating.router, prefix='/api')


@app.on_event("startup")
async def startup():
    """
    This function is an event handler that runs when the FastAPI application starts up. It initializes a connection to a Redis server and initializes a `FastAPILimiter` instance.

    :param: None
    :return: None
    :raises: None
    """
    r = await redis.Redis(host=config.REDIS_DOMAIN, port=config.REDIS_PORT, db=0,
                          password=config.REDIS_PASSWORD, encoding="utf-8",
                          decode_responses=True)
    await FastAPILimiter.init(r)


@app.get("/")
def root():
    """
    Root endpoint that returns a welcome message.
    :param: None
    :return: A dictionary with a welcome message.
    :rtype: dict
   """
    return {"message": "Contact Book"}


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
