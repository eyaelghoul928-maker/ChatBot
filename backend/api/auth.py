from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from jose import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

FAKE_USERS = {
    "demo@chatbot.tn":  {"id": 1, "role": "user",  "password": "$2b$12$OKHFXQhOs9rHrWgZn4E9m.Jz6PlWuwNHbdmLhJz274hyZfKdyqZH6"},
"admin@chatbot.tn": {"id": 2, "role": "admin", "password": "$2b$12$OKHFXQhOs9rHrWgZn4E9m.Jz6PlWuwNHbdmLhJz274hyZfKdyqZH6"},
 
}


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str


def create_token(user_id: int, email: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {"sub": str(user_id), "email": email, "role": role, "exp": expire},
        settings.secret_key, algorithm=settings.algorithm
    )


def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    user = FAKE_USERS.get(req.email)
    if not user or not pwd_context.verify(req.password, user["password"]):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    token = create_token(user["id"], req.email, user["role"])
    return TokenResponse(access_token=token, token_type="bearer", role=user["role"])