from fastapi import FastAPI, Depends
from sqlmodel import Session, select
from contextlib import asynccontextmanager
from services import ejecutar_auditoria_ia
from models import Cliente, Llamada, Evaluacion
# Importamos nuestros propios archivos
from database import engine, get_session, create_db_and_tables
from schemas import IngestaLlamadaColly

# --- 1. CICLO DE VIDA DEL SERVIDOR ---
# Esto se ejecuta una sola vez al encender la API. 
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Llamamos a la función que conecta a PostgreSQL y crea las tablas
    create_db_and_tables()
    print("¡Servidor en línea y Base de Datos conectada!")
    yield
    print("Servidor apagado.")

# Inicializamos la aplicación FastAPI
app = FastAPI(
    title="API de QA Inteligente - Colektia",
    version="1.0.0",
    lifespan=lifespan
)

# --- 2. EL ENDPOINT DE INGESTA (Historia de Usuario 05) ---
@app.post("/api/v1/llamadas/ingesta", summary="Ingestar y guardar nueva llamada de Colly")
def recibir_llamada(
    datos: IngestaLlamadaColly,          # El Filtro (Pydantic valida el JSON aquí)
    db: Session = Depends(get_session)   # La Conexión a la BD (Se abre y se cierra sola)
):
    """
    Recibe el JSON de Colly, verifica si la empresa existe, y guarda la llamada permanentemente.
    """
    
    # PASO A: Buscar o Crear el Cliente (Empresa)
    # Buscamos en la BD si ya existe un cliente con el nombre que viene en el JSON
    statement = select(Cliente).where(Cliente.nombre_empresa == datos.Empresa)
    cliente_bd = db.exec(statement).first()

    # Si no existe, lo creamos y lo guardamos inmediatamente
    if not cliente_bd:
        cliente_bd = Cliente(nombre_empresa=datos.Empresa)
        db.add(cliente_bd)
        db.commit()
        db.refresh(cliente_bd) # Refrescamos para obtener el ID que le dio PostgreSQL

    # PASO B: Empaquetar los datos variables (Fechas y Balances)
    # Metemos todo lo que es "variable" en un diccionario para la columna JSON
    metadatos_llamada = {
        "id_colly": datos.Call_ID,
        "cuenta_cliente": datos.Cuenta,
        "estatus_colly": datos.Estatus,
        "proveedor": datos.Proveedor,
        # Convertimos la fecha de Python a texto (ISO) para poder guardarla en el JSON
        "fecha_llamada": datos.fecha_llamada.isoformat(), 
        "fecha_vencimiento": datos.fecha_vencimiento,
        "dias_mora": datos.dias_mora,
        "balances": {
            "due": datos.due_balance,
            "invoiced": datos.invoiced_balance,
            "total": datos.total_balance
        }
    }

    # PASO C: Crear el registro de la Llamada
    # Usamos nuestro modelo de SQLModel y le pasamos los datos
    nueva_llamada = Llamada(
        cliente_id=cliente_bd.id, # El ID del cliente que buscamos/creamos arriba
        call_id_origen=datos.Call_ID,
        grabacion_url=datos.Grabacion,
        transcripcion=datos.Transcrip,
        metadatos_json=metadatos_llamada
    )

    # PASO D: Guardar permanentemente en PostgreSQL
    db.add(nueva_llamada)
    db.commit()
    db.refresh(nueva_llamada)

    # PASO E: LA MAGIA DE LA IA (Se ejecuta automáticamente)
    # =========================================================
    try:
        print(f"Iniciando auditoría IA para el cliente: {cliente_bd.nombre_empresa}")
        
        # 1. Llamamos a Gemini
        resultado_ia = ejecutar_auditoria_ia(
            transcripcion=nueva_llamada.transcripcion,
            llamada=nueva_llamada,
            cliente=cliente_bd
        )
        
        # 2. Sumamos los puntos obtenidos
        puntos = (
            resultado_ia.get("Saludo", 0) +
            resultado_ia.get("Confirmacion_identidad", 0) +
            resultado_ia.get("Entrega_mensaje", 0) +
            resultado_ia.get("Negociacion", 0) +
            resultado_ia.get("Agenda_compromiso", 0) +
            resultado_ia.get("Cierre", 0)
        )

        # 3. Guardamos el resultado de la IA
        nueva_evaluacion = Evaluacion(
            llamada_id=nueva_llamada.id,
            saludo_inicial=(resultado_ia.get("Saludo") == 1),
            confirmacion_identidad=(resultado_ia.get("Confirmacion_identidad") == 1),
            entrega_mensaje=(resultado_ia.get("Entrega_mensaje") == 1),
            negociacion=(resultado_ia.get("Negociacion") == 1),
            agenda_compromiso=(resultado_ia.get("Agenda_compromiso") == 1),
            cierre=(resultado_ia.get("Cierre") == 1),
            resumen_auditoria=resultado_ia.get("Resumen", "Sin resumen"),
            estado_auditoria=resultado_ia.get("Estatus_detectado", "Desconocido"),
            puntaje_logrado=puntos
        )
        
        db.add(nueva_evaluacion)
        db.commit()
        print("Evaluación de IA guardada con éxito.")
        
    except Exception as e:
        # Usamos try/except porque si Gemini se cae o el internet falla, 
        # no queremos que se pierda la llamada que ya guardamos en el Paso D.
        print(f"Error en la evaluación de IA: {e}")
    # =========================================================

    # PASO F: Responder éxito al sistema que envió la llamada
    return {
        "estado": "éxito",
        "mensaje": "Llamada procesada y guardada correctamente",
        "id_interno": nueva_llamada.id,
        "empresa": cliente_bd.nombre_empresa
    }