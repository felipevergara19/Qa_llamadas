from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

# Este modelo define exactamente qué esperamos recibir de Colly
class IngestaLlamadaColly(BaseModel):
    Call_ID: str
    Empresa: str
    Estatus: str
    Cuenta: str
    Grabacion: str
    Transcrip: str
    Proveedor: str
    fecha_llamada: datetime = Field(alias="createdTime")
    fecha_vencimiento: Optional[str] = Field(default=None, alias="Fecha de vencimiento")
    
    # Estos campos son opcionales porque a veces podrían no venir
    dias_mora: Optional[str] = Field(default=None, alias="Días de mora")
    due_balance: Optional[str] = Field(default=None, alias="Saldo vencido")
    invoiced_balance: Optional[str] = Field(default=None, alias="Saldo facturado")
    total_balance: Optional[str] = Field(default=None, alias="Saldo total")

    # Si Colly envía basura extra (como UUID o Hora envio), FastAPI la ignorará en vez de fallar
    # Configuración especial para manejar los nombres de campo con espacios
    model_config = ConfigDict(
        extra='ignore', # Ignora campos basura como "Hora envio UTC" o "UUID"
        populate_by_name=True # Permite usar los alias con espacios
    )