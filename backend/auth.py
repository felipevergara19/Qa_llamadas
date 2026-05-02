"""
auth.py — HU01: Autenticacion JWT + control de roles
"""
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Session, select

from database import get_session
from models import Usuario, RolUsuario

# ── Configuracion ──────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "colektia-qa-secret-key-cambiar-en-produccion")
ALGORITHM  = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

pwd_context    = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme  = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ── Utilidades de password ─────────────────────────────────────────────────────
def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT ────────────────────────────────────────────────────────────────────────
def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


# ── Dependencia: usuario autenticado ──────────────────────────────────────────
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_session),
) -> Usuario:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload  = decode_token(token)
        user_id  = int(payload.get("sub", 0))
    except (JWTError, ValueError):
        raise exc

    user = db.exec(select(Usuario).where(Usuario.id == user_id)).first()
    if not user or not user.activo:
        raise exc
    return user


# ── Dependencias de rol ───────────────────────────────────────────────────────
def require_roles(*roles: RolUsuario):
    """Fabrica de dependencias: require_roles('admin', 'analista_qa')"""
    def _check(current_user: Usuario = Depends(get_current_user)):
        if current_user.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rol '{current_user.rol}' no tiene permiso para esta accion",
            )
        return current_user
    return _check


# Atajos utiles
require_admin     = require_roles(RolUsuario.admin)
require_qa_or_admin = require_roles(RolUsuario.admin, RolUsuario.analista_qa)
