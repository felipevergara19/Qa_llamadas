from typing import Optional, Dict, Any, List
from sqlmodel import Field, SQLModel, Column, JSON, Relationship
from sqlalchemy import Column, Integer, ForeignKey, JSON, Float
from enum import Enum


# --- ENUM: ROLES DE USUARIO ---
class RolUsuario(str, Enum):
    admin       = "admin"        # Acceso total
    analista_qa = "analista_qa"  # Puede auditar y validar
    kam         = "kam"          # Key Account Manager, ve sus clientes
    cliente     = "cliente"      # Solo ve sus propias llamadas

# --- TABLA 0: USUARIOS (Autenticación y Roles) ---
# HU01: Login por roles | HU02: Multi-tenant | HU03: Gestión de usuarios
class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str                          # Contraseña hasheada con bcrypt
    nombre: str
    rol: RolUsuario = Field(default=RolUsuario.analista_qa)
    # Si rol = 'cliente' o 'kam', se vincula a una empresa específica
    # Si rol = 'admin' o 'analista_qa', este campo es NULL (acceso global)
    cliente_id: Optional[int] = Field(default=None, foreign_key="cliente.id")
    activo: bool = Field(default=True)


# --- TABLA 1: CLIENTES (Empresas como Sistecredito o Rapicredit) ---
class Cliente(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre_empresa: str = Field(index=True, unique=True) # Ej: "Access Finance", "Sistecredito"
    
    # --- NUEVOS CAMPOS: EL LIBRETO / GUION ---
    pais: Optional[str] = None
    medio_de_pago: Optional[str] = None
    
    # Pasos de la auditoría
    guion_identificacion: Optional[str] = None
    guion_saludo: Optional[str] = None
    guion_entrega_mensaje: Optional[str] = None
    guion_negociacion: Optional[str] = None
    guion_agenda_compromiso: Optional[str] = None
    guion_cierre: Optional[str] = None
    
    # Reglas extras (Severidades, Fix transversales)
    reglas_adicionales: Optional[str] = None

# --- TABLA 2: LLAMADAS ---
class Llamada(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Llave Foránea: Vinculamos esta llamada a la empresa correspondiente
    cliente_id: int = Field(foreign_key="cliente.id")
    
    # Datos Críticos
    call_id_origen: str
    grabacion_url: str
    transcripcion: str
    
    # La Bóveda Flexible: Aquí guardaremos fechas, balances, proveedor, etc.
    # Usamos Column(JSON) para decirle a PostgreSQL que esto es un diccionario dinámico
    metadatos_json: Dict[Any, Any] = Field(default_factory=dict, sa_column=Column(JSON))

# --- TABLA 3: EVALUACION LLAMADAS ---
class Evaluacion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    llamada_id: int = Field(foreign_key="llamada.id", unique=True)  # 1:1 con Llamada

    # Almacenamos el detalle de los criterios dinámicamente como JSON
    detalles_json: Dict[Any, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    resumen_auditoria: str  # <--- Aquí la IA escribe su análisis
    puntaje_logrado: int    # <--- La suma de los "True"
    estado_auditoria: str   # <--- "Correcto" o "Incorrecto"
    error_critico: bool = Field(default=False)  # Si se gatilló alguna severidad

    # HU22 / HU23: Validación humana (Human-in-the-Loop)
    # estado_validacion: 'pendiente' → 'aprobada' | 'rechazada'
    estado_validacion: str = Field(default="pendiente")
    validado_por_id: Optional[int] = Field(default=None, foreign_key="usuario.id")
    comentario_auditor: Optional[str] = None  # Feedback del analista QA

# --- TABLA 4: GUIONES CLIENTES ---
# NOTA: Tabla reservada para Sprint 4 (HU25 - Gestión de guiones por cliente vía UI).
# Actualmente los guiones se almacenan directamente en el modelo Cliente.
class GuionCliente(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(index=True, unique=True) # Ejemplo: "VANA", "KUESKI"
    guion_auditoria: str # Aquí guardamos las reglas específicas que leíste en tu prompt

class Criterio(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str  # Ej: "Saludo Inicial"
    descripcion: str  # Lo que la IA debe buscar
    peso: int = Field(default=1) # HU10: Importancia del punto
    es_severidad: bool = Field(default=False) # Si es True, no suma puntos, pero si falla marca error crítico
    rubrica_id: int = Field(foreign_key="rubrica.id")
    rubrica: "Rubrica" = Relationship(back_populates="criterios")

class Rubrica(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str  # Ej: "Cobranza Temprana - Access"
    empresa: str = Field(index=True)  # Nombre de empresa — coincide con Cliente.nombre_empresa
    mora_min: Optional[int] = Field(default=0)
    mora_max: Optional[int] = Field(default=9999)
    activo: bool = Field(default=True)
    criterios: List[Criterio] = Relationship(back_populates="rubrica")

class ConfiguracionSistema(SQLModel, table=True):
    clave: str = Field(primary_key=True)
    valor: str