from typing import Optional, Dict, Any, List
from sqlmodel import Field, SQLModel, Column, JSON, Relationship
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
    llamada_id: int = Field(foreign_key="llamada.id")
    
    # Almacenamos el detalle de los criterios dinámicamente como JSON
    detalles_json: Dict[Any, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    resumen_auditoria: str  # <--- Aquí la IA escribe su análisis
    puntaje_logrado: int    # <--- La suma de los "True"
    estado_auditoria: str   # <--- "Correcto" o "Incorrecto"
    error_critico: bool = Field(default=False) # Si se gatilló alguna severidad

# --- TABLA 4: GUIONES CLIENTES ---
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
    empresa: str # Para vincular con la llamada
    mora_min: Optional[int] = Field(default=0)
    mora_max: Optional[int] = Field(default=9999)
    activo: bool = Field(default=True)
    criterios: List[Criterio] = Relationship(back_populates="rubrica")

class ConfiguracionSistema(SQLModel, table=True):
    clave: str = Field(primary_key=True)
    valor: str