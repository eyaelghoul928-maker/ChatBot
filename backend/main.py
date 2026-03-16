"""
main.py — Backend FastAPI universel
Découvre le schéma de la base au démarrage et initialise le pipeline IA.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from loguru import logger
from api.auth import router as auth_router
from api.chat import router as chat_router
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Backend démarrage — DB: {settings.db_name} — ENV: {settings.db_env}")

    # Attendre que le MCP Server soit prêt, puis découvrir le schéma
    from services.ia_service import discover_schema
    for attempt in range(5):
        schema = await discover_schema()
        if schema and "Erreur" not in schema and "non disponible" not in schema:
            logger.info(f"Schéma IA initialisé avec succès")
            break
        logger.warning(f"MCP Server pas encore prêt (tentative {attempt+1}/5)...")
        await asyncio.sleep(2)

    logger.info("Backend prêt ✅")
    yield
    logger.info("Backend arrêté")


app = FastAPI(
    title="Chatbot IA — Base Universelle",
    version="2.0.0",
    description="Chatbot IA qui s'adapte à n'importe quelle base MariaDB",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router)


@app.get("/health")
async def health():
    from services.ia_service import get_schema
    schema = get_schema()
    return {
        "status": "ok",
        "version": "2.0.0",
        "env": settings.db_env,
        "db": settings.db_name,
        "schema_loaded": len(schema) > 50,
    }


@app.get("/schema")
async def schema_info():
    """Voir le schéma tel que GPT-4o le voit."""
    from services.ia_service import get_schema
    return {"schema": get_schema()}