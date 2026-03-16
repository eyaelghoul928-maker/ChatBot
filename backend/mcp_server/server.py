"""
mcp_server/server.py — Serveur MCP universel
Gère la sécurité SQL et expose le schéma automatiquement.
"""
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from contextlib import asynccontextmanager
from loguru import logger
from typing import Optional
import time

from .validator import SQLValidator
from .schema_inspector import get_full_schema
from config import settings

validator = SQLValidator()
_cached_schema = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _cached_schema
    logger.info("MCP Server démarrage...")
    try:
        _cached_schema = await get_full_schema()
        nb = _cached_schema.get("nb_tables", 0)
        logger.info(f"Schéma découvert: {nb} tables")
    except Exception as e:
        logger.error(f"Erreur découverte schéma: {e}")
        _cached_schema = {"schema": "Erreur", "nb_tables": 0}
    logger.info("MCP Server prêt — port 9000")
    yield
    logger.info("MCP Server arrêté")


mcp_app = FastAPI(title="MCP Server", version="1.0.0", lifespan=lifespan)


class QueryRequest(BaseModel):
    sql: str
    user_id: int
    user_role: str = "user"


class QueryResponse(BaseModel):
    data: list
    count: int
    temps_ms: float
    sql_used: str


def check_key(x_internal_key: Optional[str]):
    if settings.mcp_internal_key and x_internal_key != settings.mcp_internal_key:
        raise HTTPException(status_code=403, detail="Clé interne invalide")


@mcp_app.post("/execute", response_model=QueryResponse)
async def execute(req: QueryRequest, x_internal_key: Optional[str] = Header(None)):
    check_key(x_internal_key)
    t = time.time()

    v = validator.validate(req.sql, req.user_role, req.user_id)
    if not v["valid"]:
        raise HTTPException(status_code=403, detail=f"Requête refusée: {v['reason']}")

    try:
        from .executor import execute_query
        rows, columns = await execute_query(v["sql"])
        data = [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur DB: {str(e)}")

    temps_ms = round((time.time() - t) * 1000, 2)
    logger.info(f"[MCP] OK {len(data)} lignes | {temps_ms}ms")
    return QueryResponse(data=data, count=len(data), temps_ms=temps_ms, sql_used=v["sql"])


@mcp_app.post("/schema")
async def schema(x_internal_key: Optional[str] = Header(None)):
    """Retourne le schéma complet de la base — utilisé par ia_service au démarrage."""
    check_key(x_internal_key)
    if _cached_schema:
        return _cached_schema
    try:
        result = await get_full_schema()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@mcp_app.get("/health")
async def health():
    nb = _cached_schema.get("nb_tables", 0) if _cached_schema else 0
    return {"status": "ok", "service": "mcp-server", "nb_tables": nb}