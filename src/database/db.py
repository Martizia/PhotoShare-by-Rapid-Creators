import contextlib
import logging

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
import redis.asyncio as redis


from src.config.config import config
logger = logging.getLogger(f"{config.APP_NAME}.{__name__}")


class DataBaseSessionManager:
    def __init__(self, url: str):
        self._engine: AsyncEngine | None = create_async_engine(url)
        self._session_maker: async_sessionmaker = async_sessionmaker(
            autoflush=False, autocommit=False, bind=self._engine
        )

    @contextlib.asynccontextmanager
    async def session(self):
        if self._session_maker is None:
            raise Exception("Session is not initialized")
        session = self._session_maker()
        try:
            yield session
            await session.rollback()
        finally:
            await session.close()


sessionmanager = DataBaseSessionManager(config.DATABASE_URL)


def get_db():
    db = DBSession()
    try:
        yield db
    except SQLAlchemyError as err:
        print("SQLAlchemyError:", err)
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    finally:
        db.close()


def create_redis():
    return redis.ConnectionPool(
        host=config.REDIS_DOMAIN,
        port=config.REDIS_PORT,
        password=config.REDIS_PASSWORD,
        db=0,
        decode_responses=False,
    )


def get_redis() -> redis.Redis | None:
    # Here, we re-use our connection pool
    # not creating a new one
    try:
        logger.debug("get_redis connection_pool")
        if redis_pool:
            connection = redis.Redis(connection_pool=redis_pool)
            return connection
        logger.debug("get_redis connection_pool None")
    except:
        logger.debug("get_redis except")


async def check_redis() -> bool | None:
    try:
        logger.debug("check_redis")
        r: redis.Redis | None = get_redis()
        if r:
            return await r.ping()
    except Exception:
        logger.debug("check_redis fail")
        return None

redis_pool: redis.ConnectionPool = create_redis()
