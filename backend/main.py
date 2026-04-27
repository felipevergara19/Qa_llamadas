from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
from sqlmodel import Session, select, func
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from services import ejecutar_auditoria_ia
from models import Cliente, Llamada, Evaluacion, Criterio, Rubrica, ConfiguracionSistema
# Importamos nuestros propios archivos
from database import engine, get_session, create_db_and_tables
from schemas import IngestaLlamadaColly
from typing import List
from pydantic import BaseModel

# --- CONFIGURACIÓN DE LOGS AVANZADA ---
# Esto creará un archivo llamado "api_seguridad.log" en tu carpeta
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("api_seguridad.log", encoding="utf-8"), # Lo guarda en un archivo físico
        logging.StreamHandler() # También lo sigue mostrando en tu terminal
    ]
)
logger = logging.getLogger(__name__)

class CriterioCreate(BaseModel):
    nombre: str
    descripcion: str
    peso: int = 1

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

# Configuración CORS para permitir peticiones del frontend (Vite por defecto usa 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        
        # 0. Obtener el prompt base desde la BD
        statement_prompt = select(ConfiguracionSistema).where(ConfiguracionSistema.clave == "PROMPT_BASE")
        config_prompt = db.exec(statement_prompt).first()
        prompt_base_str = config_prompt.valor if config_prompt else None

        # 1. Llamamos a Gemini
        resultado_ia, puntos, error_critico = ejecutar_auditoria_ia(
            transcripcion=nueva_llamada.transcripcion,
            llamada=nueva_llamada,
            cliente=cliente_bd,
            db=db,
            prompt_base=prompt_base_str
        )

        # 3. Guardamos el resultado de la IA
        nueva_evaluacion = Evaluacion(
            llamada_id=nueva_llamada.id,
            detalles_json=resultado_ia,
            resumen_auditoria=resultado_ia.get("Resumen", "Sin resumen"),
            estado_auditoria=resultado_ia.get("Estatus_detectado", "Desconocido"),
            puntaje_logrado=puntos,
            error_critico=error_critico
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

# --- 3. HU19: VISTA DETALLE DE AUDITORÍA ---
@app.get("/api/v1/evaluaciones/{llamada_id}", summary="Obtener detalle completo de una auditoría")
def obtener_detalle_evaluacion(
    llamada_id: int, 
    db: Session = Depends(get_session)
):
    """
    Busca una llamada por su ID y devuelve toda su información junto con 
    la evaluación de la IA y los datos del cliente.
    """
    # Buscamos la Llamada, la Evaluación y el Cliente uniendo las tablas
    statement = (
        select(Llamada, Evaluacion, Cliente)
        .join(Evaluacion)
        .join(Cliente, Llamada.cliente_id == Cliente.id)
        .where(Llamada.id == llamada_id)
    )
    
    resultado = db.exec(statement).first()

    # Si alguien busca un ID que no existe, lanzamos un error 404
    if not resultado:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")

    # Separamos los 3 objetos que nos devolvió la base de datos
    llamada, evaluacion, cliente = resultado

    # Empaquetamos todo en un JSON para el Frontend
    return {
        "id_auditoria": evaluacion.id,
        "cliente": cliente.nombre_empresa,
        "fecha_llamada": llamada.metadatos_json.get("fecha_llamada"),
        "datos_colly": {
            "estatus_original": llamada.metadatos_json.get("estatus_colly"),
            "dias_mora": llamada.metadatos_json.get("dias_mora"),
            "deuda_total": llamada.metadatos_json.get("balances", {}).get("total")
        },
        "resultados_ia": {
            "estatus_detectado": evaluacion.estado_auditoria,
            "puntaje_total": evaluacion.puntaje_logrado,
            "error_critico": evaluacion.error_critico,
            "resumen_analisis": evaluacion.resumen_auditoria
        },
        "rubrica_detallada": evaluacion.detalles_json,
        "transcripcion_completa": llamada.transcripcion
    }

# --- 4. HU17: DASHBOARD DE KPIs GLOBALES ---
@app.get("/api/v1/dashboard", summary="Obtener métricas globales para gráficos")
def obtener_kpis_dashboard(db: Session = Depends(get_session)):
    """
    Calcula los KPIs generales de toda la operación:
    Total de llamadas, calidad promedio y distribución de estatus.
    """
    # 1. Total de llamadas evaluadas
    total_evaluaciones = db.exec(select(func.count(Evaluacion.id))).first() or 0

    # 2. Promedio de calidad (Puntaje)
    promedio_puntaje = db.exec(select(func.avg(Evaluacion.puntaje_logrado))).first() or 0.0

    # 3. Distribución de Estatus (Agrupamos y contamos)
    statement_estatus = (
        select(Evaluacion.estado_auditoria, func.count(Evaluacion.id))
        .group_by(Evaluacion.estado_auditoria)
    )
    distribucion_bd = db.exec(statement_estatus).all()
    
    # Convertimos el resultado de la BD a un diccionario limpio
    distribucion_dict = {estatus: cantidad for estatus, cantidad in distribucion_bd}

    # Empaquetamos todo para el gráfico del frontend
    return {
        "kpis_globales": {
            "total_llamadas_auditadas": total_evaluaciones,
            "calidad_promedio": round(promedio_puntaje, 2), # Redondeamos a 2 decimales
            "puntaje_maximo_posible": 6 # Son 6 pasos en la rúbrica
        },
        "distribucion_estatus": distribucion_dict
    }

# --- HU06: VALIDACIÓN DE ESQUEMA (Intercepción de errores) ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Atrapa cualquier JSON mal formado antes de que toque la base de datos,
    registra la alerta en el log del sistema y devuelve un error 422 claro.
    """
    # 1. Extraemos qué fue exactamente lo que intentaron enviar
    cuerpo_recibido = await request.body()
    
    # 2. Generamos el LOG de alerta para el sistema/terminal
    logger.error("🚨 [HU06 ALERTA] Se rechazó un JSON mal formado.")
    logger.error(f"URL de intento: {request.url}")
    logger.error(f"Errores detallados: {exc.errors()}")
    logger.error(f"JSON recibido: {cuerpo_recibido.decode('utf-8')}")
    
    # 3. Devolvemos la respuesta al sistema origen (ej. Colly) rechazando la carga
    return JSONResponse(
        status_code=422,
        content={
            "estado": "error",
            "mensaje": "Ingesta rechazada. El JSON no cumple con la estructura requerida.",
            "detalles": exc.errors()
        }
    )

# --- HU07: LISTADO HISTÓRICO DE LLAMADAS ---
@app.get("/api/v1/llamadas", summary="Listado histórico de llamadas auditadas")
def listar_llamadas(db: Session = Depends(get_session)):
    """
    Devuelve una lista resumida de todas las llamadas procesadas,
    ordenadas de la más reciente a la más antigua.
    Ideal para la tabla del Dashboard (Frontend).
    """
    # 1. Hacemos la consulta uniendo la Llamada con su Evaluación (si la tiene)
    # y ordenamos por el ID de forma descendente (los más nuevos primero)
    statement = (
        select(Llamada, Evaluacion)
        .join(Evaluacion, Llamada.id == Evaluacion.llamada_id, isouter=True) 
        .order_by(Llamada.id.desc())
    )
    
    resultados_bd = db.exec(statement).all()

    # 2. Formateamos la respuesta para que el Frontend la lea fácil
    lista_historial = []
    
    for llamada, evaluacion in resultados_bd:
        # Extraemos la empresa y fecha desde los metadatos JSON de forma segura
        metadatos = llamada.metadatos_json or {}
        
        item = {
            "id_llamada": llamada.id,
            "empresa": metadatos.get("Empresa", "Desconocida"),
            "fecha_llamada": metadatos.get("Fecha", "Sin fecha"),
            "estatus_original": metadatos.get("Estatus", "Desconocido"),
            "resultados_ia": {
                "estatus_ia": evaluacion.estado_auditoria if evaluacion else "Pendiente",
                "puntaje": evaluacion.puntaje_logrado if evaluacion else 0
            }
        }
        lista_historial.append(item)

    # 3. Devolvemos el total y la lista
    return {
        "total_registros": len(lista_historial),
        "data": lista_historial
    }

@app.post("/api/v1/rubricas", summary="HU09: Crear una nueva rúbrica con criterios")
def crear_rubrica(nombre: str, empresa: str, puntos: List[CriterioCreate], db: Session = Depends(get_session)):
    # 1. Crear la cabecera de la rúbrica
    nueva_rubrica = Rubrica(nombre=nombre, empresa=empresa)
    db.add(nueva_rubrica)
    db.commit()
    db.refresh(nueva_rubrica)
    
    # 2. Crear los criterios asociados
    for p in puntos:
        nuevo_criterio = Criterio(
            nombre=p.nombre,
            descripcion=p.descripcion,
            peso=p.peso,
            rubrica_id=nueva_rubrica.id
        )
        db.add(nuevo_criterio)
    
    db.commit()
    return {"mensaje": "Rúbrica creada con éxito", "id": nueva_rubrica.id}

@app.get("/api/v1/rubricas", summary="HU29: Listar todas las rúbricas")
def listar_rubricas(db: Session = Depends(get_session)):
    statement = select(Rubrica)
    resultados = db.exec(statement).all()
    lista = []
    for r in resultados:
        criterios = db.exec(select(Criterio).where(Criterio.rubrica_id == r.id)).all()
        lista.append({
            "id": r.id,
            "nombre": r.nombre,
            "empresa": r.empresa,
            "activo": r.activo,
            "criterios": [{"nombre": c.nombre, "descripcion": c.descripcion, "peso": c.peso} for c in criterios]
        })
    return lista

class PromptUpdate(BaseModel):
    texto: str

@app.get("/api/v1/config/prompt", summary="HU26: Obtener el prompt actual de la IA")
def obtener_prompt(db: Session = Depends(get_session)):
    statement = select(ConfiguracionSistema).where(ConfiguracionSistema.clave == "PROMPT_BASE")
    config = db.exec(statement).first()
    if config:
        return {"prompt": config.valor}
    
    prompt_default = """Eres un auditor automático de calidad de llamadas de cobranza de COLEKTIA.
    
DATOS DE LA LLAMADA:
- ID: {llamada_id}
- Cliente: {cliente_nombre}
- Estatus original: {estatus_original}

GUION ESPECÍFICO PARA ESTE CLIENTE:
{guion_dinamico}

TRANSCRIPCIÓN:
"{transcripcion}"

Recibirás un registro de llamada con esta información...
(Puedes agregar aquí el resto de las instrucciones de QA)
"""
    return {"prompt": prompt_default}

@app.post("/api/v1/config/prompt", summary="HU26: Actualizar el prompt base de la IA")
def actualizar_prompt(datos: PromptUpdate, db: Session = Depends(get_session)):
    statement = select(ConfiguracionSistema).where(ConfiguracionSistema.clave == "PROMPT_BASE")
    config = db.exec(statement).first()
    if config:
        config.valor = datos.texto
        db.add(config)
    else:
        nueva_config = ConfiguracionSistema(clave="PROMPT_BASE", valor=datos.texto)
        db.add(nueva_config)
    
    db.commit()
    return {"mensaje": "Prompt actualizado con éxito"}
