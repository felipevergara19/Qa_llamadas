from typing import Optional, Dict, Any
from sqlmodel import Field, SQLModel, Column, JSON

# --- TABLA 1: CLIENTES (Empresas como Sistecredito o Rapicredit) ---
class Cliente(SQLModel, table=True):
    # primary_key=True hace que PostgreSQL le asigne el ID 1, 2, 3 automáticamente
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre_empresa: str = Field(index=True) # index=True hace que buscar por nombre sea súper rápido

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