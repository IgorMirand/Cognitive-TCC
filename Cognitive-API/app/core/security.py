import bcrypt
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

# ---------------------------------------------------------------------------
# Senha
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ---------------------------------------------------------------------------
# API Key global — protege TODAS as rotas contra acesso externo não autorizado
# ---------------------------------------------------------------------------

def verify_api_key(x_api_key: str = Header(...)):
    """
    Dependência FastAPI. Exige o header:  X-Api-Key: <valor do .env API_KEY>
    Coloque em APIRouter ou em cada rota com:  dependencies=[Depends(verify_api_key)]
    """
    if not settings.API_KEY:
        raise HTTPException(status_code=500, detail="API_KEY não configurada no servidor.")
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="API Key inválida ou ausente.")


# ---------------------------------------------------------------------------
# JWT — identifica o usuário logado nas rotas sensíveis
# ---------------------------------------------------------------------------

_bearer = HTTPBearer()


def create_access_token(user_id: int, user_type: str) -> str:
    """Gera um JWT com validade definida em settings.JWT_EXPIRE_HOURS."""
    if not settings.JWT_SECRET:
        raise RuntimeError("JWT_SECRET não configurada no servidor.")

    payload = {
        "sub": str(user_id),
        "user_type": user_type,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    """
    Dependência FastAPI. Exige o header:  Authorization: Bearer <token>
    Retorna {"user_id": int, "user_type": str} se o token for válido.
    Use em rotas com:  current_user: dict = Depends(get_current_user)
    """
    if not settings.JWT_SECRET:
        raise HTTPException(status_code=500, detail="JWT_SECRET não configurada no servidor.")
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return {"user_id": int(payload["sub"]), "user_type": payload["user_type"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado. Faça login novamente.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido.")


def require_psicologo(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependência extra: garante que só psicólogos acessem a rota."""
    if current_user["user_type"] not in ("Psicologo", "Psicólogo"):
        raise HTTPException(status_code=403, detail="Acesso restrito a psicólogos.")
    return current_user


def require_paciente(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependência extra: garante que só pacientes acessem a rota."""
    if current_user["user_type"] != "Paciente":
        raise HTTPException(status_code=403, detail="Acesso restrito a pacientes.")
    return current_user