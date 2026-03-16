from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from config import settings
from loguru import logger
import asyncio
import time


_engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=True,
)


async def execute_query(sql: str) -> tuple:
    timeout = settings.bigdata_timeout_sec if settings.is_bigdata else 5.0

    t_start = time.time()

    async def _run():
        async with _engine.connect() as conn:
            result = await conn.execute(text(f"/* chatbot_mcp */ {sql}"))
            rows = result.fetchall()
            columns = list(result.keys())
            return rows, columns

    try:
        rows, columns = await asyncio.wait_for(_run(), timeout=timeout)
        elapsed = round((time.time() - t_start) * 1000, 2)
        logger.info(f"[EXECUTOR] {len(rows)} lignes | {elapsed}ms")
        return rows, columns

    except asyncio.TimeoutError:
        raise Exception(f"Timeout depasse ({timeout}s). Requete trop complexe.")