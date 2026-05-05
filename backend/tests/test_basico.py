"""
test_basico.py -- Suite de pruebas basicas para la Plataforma QA de Llamadas.

Cubre 3 areas funcionales:
  - HU01: Autenticacion con JWT
  - HU05: Ingesta de llamadas desde sistema externo
  - HU27: Re-auditoria individual de llamadas

Ejecutar con cobertura:
  pytest tests/test_basico.py -v --cov=. --cov-report=term-missing
  pytest tests/test_basico.py -v --cov=. --cov-report=html
"""

import sys
import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlmodel import create_engine, Session, SQLModel
from sqlmodel.pool import StaticPool

# ── Apuntar al directorio backend para que los imports funcionen ──────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Reemplazar engine de PostgreSQL por SQLite en memoria ANTES de importar main
import database
database.engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

import main as _app_module
from database import get_session

# ── Crear todas las tablas en SQLite ─────────────────────────────────────────
SQLModel.metadata.create_all(database.engine)


# =============================================================================
# Utilidades compartidas
# =============================================================================

def get_client():
    """Devuelve un TestClient con sesion SQLite y scheduler mockeado."""
    def _override():
        with Session(database.engine) as s:
            yield s

    _app_module.app.dependency_overrides[get_session] = _override

    with patch.object(_app_module.scheduler, "start"), \
         patch.object(_app_module.scheduler, "shutdown"), \
         patch("main.create_db_and_tables"):
        client = TestClient(_app_module.app, raise_server_exceptions=True)
        return client


def obtener_token_admin(client: TestClient) -> str:
    """Crea el usuario admin (si no existe) y retorna su JWT."""
    client.post("/api/v1/auth/seed-admin")          # ignora error si ya existe
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@colektia.com", "password": "Admin1234!"},
    )
    return resp.json()["access_token"]


# Payload valido que simula lo que envia el sistema Colly
PAYLOAD_LLAMADA = {
    "Call_ID":              "CALL-BASICO-001",
    "Empresa":              "Access Finance",
    "Estatus":              "Comprometido",
    "Cuenta":               "CTA-11111",
    "Grabacion":            "https://storage.test/basico-001.mp3",
    "Transcrip":            "Agent: Buenos dias. Debtor: Hola. Agent: Tiene saldo pendiente.",
    "Proveedor":            "Colly",
    "createdTime":          "2026-05-01T10:00:00",
    "Fecha de vencimiento": "2026-04-01",
    "Dias de mora":         30,
    "Saldo vencido":        100000,
    "Saldo facturado":      100000,
    "Saldo total":          100000,
}


# =============================================================================
# GRUPO 1 — HU01: Autenticacion
# =============================================================================

def test_login_con_credenciales_validas_retorna_token():
    """
    HU01 - CA1: Un usuario registrado debe poder autenticarse
    y recibir un token JWT valido.
    """
    client = get_client()
    client.post("/api/v1/auth/seed-admin")

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@colektia.com", "password": "Admin1234!"},
    )

    assert response.status_code == 200, (
        f"Login valido debe retornar 200, se obtuvo {response.status_code}"
    )
    body = response.json()
    assert "access_token" in body, "La respuesta debe contener 'access_token'"
    assert body["token_type"] == "bearer"


def test_acceso_sin_token_retorna_401():
    """
    HU01 - CA2: Un endpoint protegido debe rechazar peticiones
    sin autenticacion con HTTP 401.
    """
    client = get_client()

    response = client.get("/api/v1/llamadas")

    assert response.status_code == 401, (
        f"Sin token debe retornar 401, se obtuvo {response.status_code}"
    )


# =============================================================================
# GRUPO 2 — HU05: Ingesta de llamadas
# =============================================================================

def test_ingesta_payload_valido_retorna_id_interno():
    """
    HU05 - CA1: El sistema debe aceptar una llamada con todos los campos
    obligatorios y retornar un identificador interno unico.
    """
    client = get_client()

    response = client.post("/api/v1/llamadas/ingesta", json=PAYLOAD_LLAMADA)

    assert response.status_code == 200, (
        f"Ingesta valida debe retornar 200, se obtuvo {response.status_code}"
    )
    body = response.json()
    assert "id_interno" in body,            "Debe retornar campo 'id_interno'"
    assert isinstance(body["id_interno"], int), "El id_interno debe ser entero"
    assert body["estado"] == "exito"


def test_ingesta_payload_incompleto_retorna_422():
    """
    HU05 - CA2: Un payload sin los campos obligatorios debe ser rechazado
    con HTTP 422 Unprocessable Entity.
    """
    client = get_client()
    payload_incompleto = {"Call_ID": "CALL-INCOMPLETO-001"}

    response = client.post("/api/v1/llamadas/ingesta", json=payload_incompleto)

    assert response.status_code == 422, (
        f"Payload incompleto debe retornar 422, se obtuvo {response.status_code}"
    )


# =============================================================================
# GRUPO 3 — HU27: Re-auditoria individual
# =============================================================================

def test_reauditoria_sin_token_retorna_401():
    """
    HU27 - CA1: El endpoint de re-auditoria es de acceso restringido.
    Sin token debe retornar HTTP 401.
    """
    client = get_client()

    response = client.post("/api/v1/auditoria/reauditar/1")

    assert response.status_code == 401, (
        f"Re-auditoria sin token debe retornar 401, se obtuvo {response.status_code}"
    )


def test_reauditoria_id_inexistente_retorna_404():
    """
    HU27 - CA2: Intentar re-auditar una llamada que no existe debe
    retornar HTTP 404 Not Found con mensaje descriptivo.
    """
    client = get_client()
    token = obtener_token_admin(client)

    response = client.post(
        "/api/v1/auditoria/reauditar/999999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404, (
        f"ID inexistente debe retornar 404, se obtuvo {response.status_code}"
    )
