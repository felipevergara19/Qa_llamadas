from typing import Optional, Dict, Any
from sqlmodel import Field, SQLModel, Column, JSON
from sqlalchemy import Column, Integer, ForeignKey, JSON, Float

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
    llamada_id: int = Field(foreign_key="llamada.id")
    
    # Marcamos cada punto de tu rúbrica como Booleano (True/False)
    saludo_inicial: bool = Field(default=False)
    confirmacion_identidad: bool = Field(default=False)
    entrega_mensaje: bool = Field(default=False)
    negociacion: bool = Field(default=False)
    agenda_compromiso: bool = Field(default=False)
    cierre: bool = Field(default=False)
    
    resumen_auditoria: str  # <--- Aquí la IA escribe su análisis
    puntaje_logrado: int    # <--- La suma de los "True"
    estado_auditoria: str   # <--- "Correcto" o "Incorrecto"

# --- TABLA 4: GUIONES CLIENTES ---
class GuionCliente(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(index=True, unique=True) # Ejemplo: "VANA", "KUESKI"
    guion_auditoria: str # Aquí guardamos las reglas específicas que leíste en tu prompt