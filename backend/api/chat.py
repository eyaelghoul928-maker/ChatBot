from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from loguru import logger
from api.auth import verify_token
from services.ia_service import run_full_pipeline
import time

router = APIRouter(prefix="/api/chat", tags=["chat"])


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    reponse: str
    sql: Optional[str] = None
    nb_resultats: int
    langue: str
    cached: bool
    temps_ms: float


@router.post("/ask", response_model=AskResponse)
async def ask(
    req: AskRequest,
    authorization: Optional[str] = Header(None)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token manquant")

    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)

    user_id = int(payload["sub"])
    user_role = payload["role"]

    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question vide")

    logger.info(f"[CHAT] User {user_id} | {req.question[:60]}")

    t_start = time.time()
    result = await run_full_pipeline(req.question, user_id, user_role)
    temps_ms = round((time.time() - t_start) * 1000, 2)

    return AskResponse(
        reponse=result["reponse"],
        sql=result.get("sql"),
        nb_resultats=result.get("nb_resultats", 0),
        langue=result.get("langue", "fr"),
        cached=result.get("cached", False),
        temps_ms=temps_ms,
    )