from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
from sqlmodel import Session, select, func
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services import ejecutar_auditoria_ia
from models import Cliente, Llamada, Evaluacion, Criterio, Rubrica, ConfiguracionSistema
from database import engine, get_session, create_db_and_tables
from schemas import IngestaLlamadaColly
from typing import List
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("api_seguridad.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CriterioCreate(BaseModel):
    nombre: str
    descripcion: str
    peso: int = 1
    es_severidad: bool = False

class RubricaCreate(BaseModel):
    nombre: str
    empresa: str
    puntos: List[CriterioCreate]

class PromptUpdate(BaseModel):
    texto: str

# =============================================================================
# HU16 - PROCESAMIENTO EN LOTE (MICRO-BATCHING)
# =============================================================================
BATCH_SIZE = 100
scheduler = AsyncIOScheduler(timezone="America/Santiago")

def procesar_llamadas_pendientes():
    logger.info(f"[BATCH] Iniciando ciclo (max {BATCH_SIZE} llamadas)...")
    with Session(engine) as db:
        ids_evaluados = select(Evaluacion.llamada_id)
        statement = (
            select(Llamada, Cliente)
            .join(Cliente, Llamada.cliente_id == Cliente.id)
            .where(~Llamada.id.in_(ids_evaluados))
            .limit(BATCH_SIZE)
        )
        pendientes = db.exec(statement).all()
        if not pendientes:
            logger.info("[BATCH] No hay llamadas pendientes.")
            return
        logger.info(f"[BATCH] Encontradas {len(pendientes)} llamadas para auditar.")
        exitosas = 0
        fallidas = 0
        for llamada, cliente in pendientes:
            try:
                config_prompt = db.exec(
                    select(ConfiguracionSistema).where(ConfiguracionSistema.clave == "PROMPT_BASE")
                ).first()
                prompt_base_str = config_prompt.valor if config_prompt else None
                resultado_ia, puntos, error_critico = ejecutar_auditoria_ia(
                    transcripcion=llamada.transcripcion,
                    llamada=llamada,
                    cliente=cliente,
                    db=db,
                    prompt_base=prompt_base_str
                )
                nueva_evaluacion = Evaluacion(
                    llamada_id=llamada.id,
                    detalles_json=resultado_ia,
                    resumen_auditoria=resultado_ia.get("Resumen", "Sin resumen"),
                    estado_auditoria=resultado_ia.get("Estatus_detectado", "Desconocido"),
                    puntaje_logrado=puntos,
                    error_critico=error_critico
                )
                db.add(nueva_evaluacion)
                db.commit()
                exitosas += 1
                logger.info(f"  OK Llamada #{llamada.id} ({cliente.nombre_empresa}) auditada.")
            except Exception as e:
                fallidas += 1
                logger.error(f"  ERROR Llamada #{llamada.id}: {e}")
        logger.info(f"[BATCH] Ciclo terminado - Exitosas: {exitosas} | Fallidas: {fallidas}")

# =============================================================================
# CICLO DE VIDA DEL SERVIDOR
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    scheduler.add_job(
        procesar_llamadas_pendientes,
        trigger="interval",
        minutes=240,
        id="auditar_pendientes",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info("Servidor en linea. Scheduler activo: auditoria cada 240 min.")
    yield
    scheduler.shutdown()
    logger.info("Servidor apagado.")

# =============================================================================
# APP FASTAPI
# =============================================================================
app = FastAPI(title="API de QA Inteligente - Colektia", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# HU05 - ENDPOINT DE INGESTA (solo guarda, no llama a IA)
# =============================================================================
@app.post("/api/v1/llamadas/ingesta", summary="HU05: Ingestar y guardar nueva llamada de Colly")
def recibir_llamada(datos: IngestaLlamadaColly, db: Session = Depends(get_session)):
    statement = select(Cliente).where(Cliente.nombre_empresa == datos.Empresa)
    cliente_bd = db.exec(statement).first()
    if not cliente_bd:
        cliente_bd = Cliente(nombre_empresa=datos.Empresa)
        db.add(cliente_bd)
        db.commit()
        db.refresh(cliente_bd)

    metadatos_llamada = {
        "id_colly": datos.Call_ID,
        "cuenta_cliente": datos.Cuenta,
        "estatus_colly": datos.Estatus,
        "proveedor": datos.Proveedor,
        "fecha_llamada": datos.fecha_llamada.isoformat(),
        "fecha_vencimiento": datos.fecha_vencimiento,
        "dias_mora": datos.dias_mora,
        "balances": {
            "due": datos.due_balance,
            "invoiced": datos.invoiced_balance,
            "total": datos.total_balance
        }
    }
    nueva_llamada = Llamada(
        cliente_id=cliente_bd.id,
        call_id_origen=datos.Call_ID,
        grabacion_url=datos.Grabacion,
        transcripcion=datos.Transcrip,
        metadatos_json=metadatos_llamada
    )
    db.add(nueva_llamada)
    db.commit()
    db.refresh(nueva_llamada)
    return {
        "estado": "exito",
        "mensaje": "Llamada recibida y encolada para auditoria automatica",
        "id_interno": nueva_llamada.id,
        "empresa": cliente_bd.nombre_empresa
    }

# =============================================================================
# HU16 - ENDPOINTS DEL BATCH
# =============================================================================
@app.post("/api/v1/auditoria/ejecutar", summary="HU16: Disparar manualmente el batch de auditoria")
def disparar_auditoria_manual(background_tasks: BackgroundTasks):
    background_tasks.add_task(procesar_llamadas_pendientes)
    return {"estado": "iniciado", "mensaje": "Procesando llamadas pendientes en segundo plano."}

@app.get("/api/v1/auditoria/estado", summary="HU16: Ver estado de la cola de auditoria")
def estado_cola_auditoria(db: Session = Depends(get_session)):
    total_llamadas = db.exec(select(func.count(Llamada.id))).first() or 0
    total_evaluadas = db.exec(select(func.count(Evaluacion.id))).first() or 0
    pendientes = total_llamadas - total_evaluadas
    job = scheduler.get_job("auditar_pendientes")
    proxima_ejecucion = str(job.next_run_time) if job and job.next_run_time else "No programada"
    return {
        "total_llamadas_recibidas": total_llamadas,
        "total_auditadas": total_evaluadas,
        "pendientes_de_auditoria": pendientes,
        "proxima_ejecucion_automatica": proxima_ejecucion
    }

# =============================================================================
# HU19 - VISTA DETALLE DE AUDITORIA
# =============================================================================
@app.get("/api/v1/evaluaciones/{llamada_id}", summary="HU19: Detalle completo de una auditoria")
def obtener_detalle_evaluacion(llamada_id: int, db: Session = Depends(get_session)):
    statement = (
        select(Llamada, Evaluacion, Cliente)
        .join(Evaluacion)
        .join(Cliente, Llamada.cliente_id == Cliente.id)
        .where(Llamada.id == llamada_id)
    )
    resultado = db.exec(statement).first()
    if not resultado:
        raise HTTPException(status_code=404, detail="Evaluacion no encontrada")
    llamada, evaluacion, cliente = resultado
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

# =============================================================================
# HU17 - DASHBOARD DE KPIs (incluye porcentaje de cobertura SLA)
# =============================================================================
@app.get("/api/v1/dashboard", summary="HU17: Metricas globales para graficos")
def obtener_kpis_dashboard(db: Session = Depends(get_session)):
    total_llamadas = db.exec(select(func.count(Llamada.id))).first() or 0
    total_evaluaciones = db.exec(select(func.count(Evaluacion.id))).first() or 0
    promedio_puntaje = db.exec(select(func.avg(Evaluacion.puntaje_logrado))).first() or 0.0
    statement_estatus = (
        select(Evaluacion.estado_auditoria, func.count(Evaluacion.id))
        .group_by(Evaluacion.estado_auditoria)
    )
    distribucion_bd = db.exec(statement_estatus).all()
    distribucion_dict = {estatus: cantidad for estatus, cantidad in distribucion_bd}
    cobertura_pct = round((total_evaluaciones / total_llamadas * 100), 1) if total_llamadas > 0 else 0.0
    return {
        "kpis_globales": {
            "total_llamadas_recibidas": total_llamadas,
            "total_llamadas_auditadas": total_evaluaciones,
            "cobertura_porcentaje": cobertura_pct,
            "calidad_promedio": round(promedio_puntaje, 2),
            "puntaje_maximo_posible": 6
        },
        "distribucion_estatus": distribucion_dict
    }

# =============================================================================
# HU06 - VALIDACION DE ESQUEMA
# =============================================================================
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    cuerpo_recibido = await request.body()
    logger.error("[HU06 ALERTA] Se rechazo un JSON mal formado.")
    logger.error(f"URL de intento: {request.url}")
    logger.error(f"Errores detallados: {exc.errors()}")
    logger.error(f"JSON recibido: {cuerpo_recibido.decode('utf-8')}")
    return JSONResponse(
        status_code=422,
        content={
            "estado": "error",
            "mensaje": "Ingesta rechazada. El JSON no cumple con la estructura requerida.",
            "detalles": exc.errors()
        }
    )

# =============================================================================
# HU07 - LISTADO HISTORICO
# =============================================================================
@app.get("/api/v1/llamadas", summary="HU07: Listado historico de llamadas")
def listar_llamadas(db: Session = Depends(get_session)):
    statement = (
        select(Llamada, Evaluacion, Cliente)
        .join(Cliente, Llamada.cliente_id == Cliente.id)
        .join(Evaluacion, Llamada.id == Evaluacion.llamada_id, isouter=True)
        .order_by(Llamada.id.desc())
    )
    resultados_bd = db.exec(statement).all()
    lista_historial = []
    for llamada, evaluacion, cliente in resultados_bd:
        metadatos = llamada.metadatos_json or {}
        item = {
            "id_llamada": llamada.id,
            "empresa": cliente.nombre_empresa,
            "fecha_llamada": metadatos.get("fecha_llamada", "Sin fecha"),
            "fecha_vencimiento": metadatos.get("fecha_vencimiento", "-"),
            "dias_mora": metadatos.get("dias_mora", 0),
            "estatus_original": metadatos.get("estatus_colly", "Desconocido"),
            "resultados_ia": {
                "estatus_ia": evaluacion.estado_auditoria if evaluacion else "Pendiente",
                "puntaje": evaluacion.puntaje_logrado if evaluacion else 0,
                "error_critico": evaluacion.error_critico if evaluacion else False
            }
        }
        lista_historial.append(item)
    return {"total_registros": len(lista_historial), "data": lista_historial}

# =============================================================================
# HU09 / HU29 - RUBRICAS
# =============================================================================
@app.post("/api/v1/rubricas", summary="HU09: Crear rubrica con criterios")
def crear_rubrica(datos: RubricaCreate, db: Session = Depends(get_session)):
    nueva_rubrica = Rubrica(nombre=datos.nombre, empresa=datos.empresa)
    db.add(nueva_rubrica)
    db.commit()
    db.refresh(nueva_rubrica)
    for p in datos.puntos:
        nuevo_criterio = Criterio(
            nombre=p.nombre,
            descripcion=p.descripcion,
            peso=p.peso,
            es_severidad=p.es_severidad,
            rubrica_id=nueva_rubrica.id
        )
        db.add(nuevo_criterio)
    db.commit()
    return {"mensaje": "Rubrica creada con exito", "id": nueva_rubrica.id}

@app.get("/api/v1/rubricas", summary="HU29: Listar todas las rubricas")
def listar_rubricas(db: Session = Depends(get_session)):
    resultados = db.exec(select(Rubrica)).all()
    lista = []
    for r in resultados:
        criterios = db.exec(select(Criterio).where(Criterio.rubrica_id == r.id)).all()
        lista.append({
            "id": r.id,
            "nombre": r.nombre,
            "empresa": r.empresa,
            "activo": r.activo,
            "criterios": [
                {"nombre": c.nombre, "descripcion": c.descripcion, "peso": c.peso, "es_severidad": c.es_severidad}
                for c in criterios
            ]
        })
    return lista

# =============================================================================
# HU26 - TUNING DE PROMPT
# =============================================================================
@app.get("/api/v1/config/prompt", summary="HU26: Obtener el prompt actual de la IA")
def obtener_prompt(db: Session = Depends(get_session)):
    config = db.exec(
        select(ConfiguracionSistema).where(ConfiguracionSistema.clave == "PROMPT_BASE")
    ).first()
    if config:
        return {"prompt": config.valor}
    prompt_default = (
        "Eres un auditor automatico de calidad de llamadas de cobranza de COLEKTIA.\n\n"
        "DATOS DE LA LLAMADA:\n- ID: {llamada_id}\n- Cliente: {cliente_nombre}\n"
        "- Estatus original: {estatus_original}\n\n"
        "GUION ESPECIFICO PARA ESTE CLIENTE:\n{guion_dinamico}\n\n"
        "TRANSCRIPCION:\n\"{transcripcion}\"\n"
    )
    return {"prompt": prompt_default}

@app.post("/api/v1/config/prompt", summary="HU26: Actualizar el prompt base de la IA")
def actualizar_prompt(datos: PromptUpdate, db: Session = Depends(get_session)):
    config = db.exec(
        select(ConfiguracionSistema).where(ConfiguracionSistema.clave == "PROMPT_BASE")
    ).first()
    if config:
        config.valor = datos.texto
        db.add(config)
    else:
        db.add(ConfiguracionSistema(clave="PROMPT_BASE", valor=datos.texto))
    db.commit()
    return {"mensaje": "Prompt actualizado con exito"}
