"""
Gestion du pool de connexions SQLAlchemy async.
S'adapte automatiquement à l'environnement (test ou Big Data).
"""
from sqlalchemy.ext.asyncio import (
    create_async_engine, AsyncSession, async_sessionmaker
)
from sqlalchemy import text, event
from config import settings
from loguru import logger
def create_db_engine():
    """
    Crée un moteur SQLAlchemy adapté à l'environnement.
    - Mode TEST     : Pool petit (5 conns), timeout court
    - Mode BIG DATA : Pool large (30 conns), optimisations Big Data
    """
    common_args = {
        "url": settings.database_url,
        "pool_recycle": settings.db_pool_recycle,
        "pool_pre_ping": True,       # Teste la connexion avant utilisation
        "echo": settings.is_test and settings.log_level == "DEBUG",
    }
    if settings.is_bigdata:
        # ── Configuration Big Data ─────────────────────────────────
        logger.info("🏭 Moteur SQLAlchemy BIG DATA — pool_size=30")
        engine = create_async_engine(
            **common_args,
            pool_size=settings.db_pool_size,      # 30 connexions
            max_overflow=settings.db_max_overflow, # +20 si besoin
            pool_timeout=settings.db_pool_timeout, # 30s avant erreur
            # Optimisations Big Data MariaDB
            connect_args={
                "charset": "utf8mb4",
                "connect_timeout": 10,
                "read_timeout": settings.bigdata_timeout_sec,
                "write_timeout": 30,
                # Active les index hints automatiques
                "init_command": (
                    "SET SESSION query_cache_type=ON; "
                    "SET SESSION sql_mode='STRICT_TRANS_TABLES';"
                ),
            }
        )
    else:
        # ── Configuration Test ─────────────────────────────────────
        logger.info("🧪 Moteur SQLAlchemy TEST — pool_size=5")
        engine = create_async_engine(
            **common_args,
            pool_size=5,
            max_overflow=5,
            pool_timeout=10,
            connect_args={"charset": "utf8mb4"},
        )
    return engine
# ── Instances globales ────────────────────────────────────────────────────
engine = create_db_engine()
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
# ── Helper pour les routes FastAPI ────────────────────────────────────────
async def get_db_session() -> AsyncSession:
    """Dependency injection pour FastAPI — session par requête."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
async def check_db_health() -> dict:
    """Vérifie la connexion DB au démarrage."""
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT VERSION() AS v"))
            version = result.scalar()
            return {
                "status": "ok",
                "version": version,
                "env": settings.db_env,
                "db": settings.db_name,
            }
    except Exception as e:
        logger.error(f"❌ DB health check failed: {e}")
        return {"status": "error", "error": str(e)}