from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security import OAuth2PasswordRequestForm
import logging
from sqlmodel import Session, select, func
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services import ejecutar_auditoria_ia
from models import Cliente, Llamada, Evaluacion, Criterio, Rubrica, ConfiguracionSistema, Usuario, RolUsuario
from database import engine, get_session, create_db_and_tables
from schemas import IngestaLlamadaColly
from typing import List, Optional
from pydantic import BaseModel
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_admin, require_qa_or_admin
)

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

class UsuarioCreate(BaseModel):
    email: str
    password: str
    nombre: str
    rol: RolUsuario = RolUsuario.analista_qa
    cliente_id: Optional[int] = None

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    rol: Optional[RolUsuario] = None
    cliente_id: Optional[int] = None
    activo: Optional[bool] = None

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
# HU27 - RE-AUDITORÍA INDIVIDUAL (validación de calidad de la IA)
# Permite al analista QA forzar una nueva auditoría sobre una llamada ya evaluada.
# Borra la evaluación anterior y genera una nueva desde cero con Gemini.
# =============================================================================
@app.post(
    "/api/v1/auditoria/reauditar/{llamada_id}",
    summary="HU27: Re-auditar una llamada ya evaluada (solo analista_qa / admin)",
)
def reauditar_llamada(
    llamada_id: int,
    db: Session = Depends(get_session),
    current_user: Usuario = Depends(require_qa_or_admin),
):
    # 1. Obtener la llamada y su cliente
    row = db.exec(
        select(Llamada, Cliente)
        .join(Cliente, Llamada.cliente_id == Cliente.id)
        .where(Llamada.id == llamada_id)
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Llamada #{llamada_id} no encontrada")
    llamada, cliente = row

    # 2. Eliminar evaluación anterior si existe
    evaluacion_anterior = db.exec(
        select(Evaluacion).where(Evaluacion.llamada_id == llamada_id)
    ).first()
    if evaluacion_anterior:
        db.delete(evaluacion_anterior)
        db.commit()
        logger.info(f"[REAUDITORIA] Evaluacion anterior de llamada #{llamada_id} eliminada por {current_user.email}")

    # 3. Ejecutar nueva auditoría con Gemini
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
            prompt_base=prompt_base_str,
        )

        nueva_evaluacion = Evaluacion(
            llamada_id=llamada.id,
            detalles_json=resultado_ia,
            resumen_auditoria=resultado_ia.get("Resumen", "Sin resumen"),
            estado_auditoria=resultado_ia.get("Estatus_detectado", "Desconocido"),
            puntaje_logrado=puntos,
            error_critico=error_critico,
            estado_validacion="pendiente",  # Resetear validación humana
        )
        db.add(nueva_evaluacion)
        db.commit()
        db.refresh(nueva_evaluacion)

        logger.info(
            f"[REAUDITORIA] Llamada #{llamada_id} re-auditada por {current_user.email} "
            f"— puntaje: {puntos} | error_critico: {error_critico}"
        )
        return {
            "estado": "completado",
            "llamada_id": llamada_id,
            "empresa": cliente.nombre_empresa,
            "puntaje_logrado": puntos,
            "error_critico": error_critico,
            "resumen": resultado_ia.get("Resumen", ""),
            "re_auditado_por": current_user.email,
        }

    except Exception as e:
        logger.error(f"[REAUDITORIA] Error en llamada #{llamada_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al re-auditar: {str(e)}")

# =============================================================================
# HU19 - VISTA DETALLE DE AUDITORIA
# =============================================================================
@app.get("/api/v1/evaluaciones/{llamada_id}", summary="HU19/HU14: Detalle completo de una auditoria con feedback por criterio")
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

    # HU14: Buscar la rúbrica activa para este cliente y días de mora
    dias_mora = llamada.metadatos_json.get("dias_mora", 0) or 0
    rubrica_activa = db.exec(
        select(Rubrica)
        .where(
            Rubrica.empresa == cliente.nombre_empresa,
            Rubrica.activo == True,
            Rubrica.mora_min <= dias_mora,
            Rubrica.mora_max >= dias_mora,
        )
    ).first()

    # Construir mapa nombre_criterio → {descripcion, peso, es_severidad}
    criterios_info = {}
    if rubrica_activa:
        criterios_bd = db.exec(
            select(Criterio).where(Criterio.rubrica_id == rubrica_activa.id)
        ).all()
        for c in criterios_bd:
            criterios_info[c.nombre] = {
                "descripcion": c.descripcion,
                "peso": c.peso,
                "es_severidad": c.es_severidad,
            }

    # HU14: Armar feedback enriquecido por criterio
    detalles = evaluacion.detalles_json or {}
    CAMPOS_META = {"Resumen", "Estatus_detectado", "Estatus_coherente", "Errores_criticos_encontrados"}
    feedback_criterios = []
    for nombre, resultado_ia in detalles.items():
        if nombre in CAMPOS_META:
            continue
        paso = resultado_ia in (1, True, "1", "true")
        info = criterios_info.get(nombre, {})
        feedback_criterios.append({
            "criterio": nombre,
            "resultado": paso,
            "descripcion": info.get("descripcion", "Sin descripcion disponible"),
            "peso": info.get("peso", 1),
            "es_severidad": info.get("es_severidad", False),
        })

    # Lista de criterios de severidad que fallaron (guardada por la IA o recalculada)
    errores_criticos = detalles.get("Errores_criticos_encontrados", [])
    # Si está vacío pero hay error_critico, recalcular desde los criterios
    if not errores_criticos and evaluacion.error_critico:
        errores_criticos = [
            item["criterio"] for item in feedback_criterios
            if item["es_severidad"] and not item["resultado"]
        ]

    return {
        "id_auditoria": evaluacion.id,
        "cliente": cliente.nombre_empresa,
        "fecha_llamada": llamada.metadatos_json.get("fecha_llamada"),
        "datos_colly": {
            "estatus_original": llamada.metadatos_json.get("estatus_colly"),
            "dias_mora": dias_mora,
            "deuda_total": llamada.metadatos_json.get("balances", {}).get("total")
        },
        "resultados_ia": {
            "estatus_detectado": evaluacion.estado_auditoria,
            "puntaje_total": evaluacion.puntaje_logrado,
            "error_critico": evaluacion.error_critico,
            "errores_criticos": errores_criticos,
            "resumen_analisis": evaluacion.resumen_auditoria,
            "estado_validacion": evaluacion.estado_validacion,
            "comentario_auditor": evaluacion.comentario_auditor,
        },
        # HU14: feedback enriquecido con descripcion por criterio
        "feedback_criterios": feedback_criterios,
        # Mantener compatibilidad con frontend anterior
        "rubrica_detallada": detalles,
        "transcripcion_completa": llamada.transcripcion
    }

# =============================================================================
# HU17 - DASHBOARD DE KPIs (incluye porcentaje de cobertura SLA)
# =============================================================================
@app.get("/api/v1/dashboard", summary="HU17: Metricas globales para graficos")
def obtener_kpis_dashboard(db: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    # HU02: Si el rol es cliente o kam, filtrar por su cliente_id
    roles_filtrados = (RolUsuario.cliente, RolUsuario.kam)
    filtro_tenant = (
        Llamada.cliente_id == current_user.cliente_id
        if current_user.rol in roles_filtrados and current_user.cliente_id
        else True
    )
    total_llamadas     = db.exec(select(func.count(Llamada.id)).where(filtro_tenant)).first() or 0
    ids_llamadas_tenant = select(Llamada.id).where(filtro_tenant)
    total_evaluaciones = db.exec(select(func.count(Evaluacion.id)).where(Evaluacion.llamada_id.in_(ids_llamadas_tenant))).first() or 0
    promedio_puntaje   = db.exec(select(func.avg(Evaluacion.puntaje_logrado)).where(Evaluacion.llamada_id.in_(ids_llamadas_tenant))).first() or 0.0
    statement_estatus  = (
        select(Evaluacion.estado_auditoria, func.count(Evaluacion.id))
        .where(Evaluacion.llamada_id.in_(ids_llamadas_tenant))
        .group_by(Evaluacion.estado_auditoria)
    )
    distribucion_dict  = {e: n for e, n in db.exec(statement_estatus).all()}
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
def listar_llamadas(db: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    # HU02: Multi-tenant — clientes y KAM solo ven sus llamadas
    roles_filtrados = (RolUsuario.cliente, RolUsuario.kam)
    base_query = (
        select(Llamada, Evaluacion, Cliente)
        .join(Cliente, Llamada.cliente_id == Cliente.id)
        .join(Evaluacion, Llamada.id == Evaluacion.llamada_id, isouter=True)
        .order_by(Llamada.id.desc())
    )
    if current_user.rol in roles_filtrados and current_user.cliente_id:
        statement = base_query.where(Llamada.cliente_id == current_user.cliente_id)
    else:
        statement = base_query
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

# =============================================================================
# HU01 - AUTENTICACION JWT
# =============================================================================
@app.post("/api/v1/auth/login", summary="HU01: Login y obtencion de token JWT")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_session),
):
    user = db.exec(select(Usuario).where(Usuario.email == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contrasena incorrectos",
        )
    if not user.activo:
        raise HTTPException(status_code=403, detail="Usuario desactivado")

    token = create_access_token({
        "sub": str(user.id),
        "rol": user.rol,
        "cliente_id": user.cliente_id,
        "nombre": user.nombre,
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "rol": user.rol,
        "nombre": user.nombre,
        "cliente_id": user.cliente_id,
    }


@app.get("/api/v1/auth/me", summary="HU01: Datos del usuario autenticado")
def me(current_user: Usuario = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "nombre": current_user.nombre,
        "rol": current_user.rol,
        "cliente_id": current_user.cliente_id,
    }


# =============================================================================
# HU03 - GESTION DE USUARIOS (solo Admin)
# =============================================================================
@app.post("/api/v1/usuarios", summary="HU03: Crear usuario (admin)")
def crear_usuario(
    datos: UsuarioCreate,
    db: Session = Depends(get_session),
    _: Usuario = Depends(require_admin),
):
    if db.exec(select(Usuario).where(Usuario.email == datos.email)).first():
        raise HTTPException(status_code=400, detail="El email ya esta registrado")
    nuevo = Usuario(
        email=datos.email,
        password_hash=hash_password(datos.password),
        nombre=datos.nombre,
        rol=datos.rol,
        cliente_id=datos.cliente_id,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return {"mensaje": "Usuario creado", "id": nuevo.id, "email": nuevo.email, "rol": nuevo.rol}


@app.get("/api/v1/usuarios", summary="HU03: Listar usuarios (admin)")
def listar_usuarios(
    db: Session = Depends(get_session),
    _: Usuario = Depends(require_admin),
):
    usuarios = db.exec(select(Usuario)).all()
    return [
        {"id": u.id, "email": u.email, "nombre": u.nombre, "rol": u.rol,
         "cliente_id": u.cliente_id, "activo": u.activo}
        for u in usuarios
    ]


@app.put("/api/v1/usuarios/{usuario_id}", summary="HU03: Actualizar usuario (admin)")
def actualizar_usuario(
    usuario_id: int,
    datos: UsuarioUpdate,
    db: Session = Depends(get_session),
    _: Usuario = Depends(require_admin),
):
    user = db.exec(select(Usuario).where(Usuario.id == usuario_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if datos.nombre    is not None: user.nombre    = datos.nombre
    if datos.rol       is not None: user.rol       = datos.rol
    if datos.cliente_id is not None: user.cliente_id = datos.cliente_id
    if datos.activo    is not None: user.activo    = datos.activo
    db.add(user)
    db.commit()
    return {"mensaje": "Usuario actualizado", "id": user.id}


@app.delete("/api/v1/usuarios/{usuario_id}", summary="HU03: Desactivar usuario (admin)")
def desactivar_usuario(
    usuario_id: int,
    db: Session = Depends(get_session),
    _: Usuario = Depends(require_admin),
):
    user = db.exec(select(Usuario).where(Usuario.id == usuario_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.activo = False
    db.add(user)
    db.commit()
    return {"mensaje": "Usuario desactivado", "id": user.id}


# =============================================================================
# HU22 - APELACIÓN DE NOTA (HITL: Human-in-the-Loop)
# Permite al analista QA o admin aprobar/rechazar la evaluación de la IA.
# =============================================================================
class ValidacionUpdate(BaseModel):
    estado: str               # "aprobada" | "rechazada" | "pendiente"
    comentario: Optional[str] = None  # Justificación del analista

@app.put(
    "/api/v1/evaluaciones/{llamada_id}/validacion",
    summary="HU22: Aprobar o rechazar la evaluación de la IA (analista_qa / admin)",
)
def actualizar_validacion(
    llamada_id: int,
    datos: ValidacionUpdate,
    db: Session = Depends(get_session),
    current_user: Usuario = Depends(require_qa_or_admin),
):
    if datos.estado not in ("aprobada", "rechazada", "pendiente"):
        raise HTTPException(status_code=400, detail="Estado inválido. Use: aprobada, rechazada o pendiente.")

    evaluacion = db.exec(
        select(Evaluacion).where(Evaluacion.llamada_id == llamada_id)
    ).first()
    if not evaluacion:
        raise HTTPException(status_code=404, detail=f"No existe evaluación para la llamada #{llamada_id}")

    evaluacion.estado_validacion  = datos.estado
    evaluacion.comentario_auditor = datos.comentario or None
    evaluacion.validado_por_id    = current_user.id
    db.add(evaluacion)
    db.commit()
    logger.info(
        f"[HU22] Llamada #{llamada_id} → '{datos.estado}' por {current_user.email} | "
        f"comentario: {datos.comentario or '—'}"
    )
    return {
        "mensaje": f"Evaluación marcada como '{datos.estado}'",
        "llamada_id": llamada_id,
        "estado_validacion": datos.estado,
        "comentario_auditor": datos.comentario,
        "validado_por": current_user.email,
    }


# =============================================================================
# HU03 - LISTAR CLIENTES (para el selector de empresa en la gestión de usuarios)
# =============================================================================
@app.get("/api/v1/clientes", summary="HU03: Listar empresas clientes (admin)")
def listar_clientes(
    db: Session = Depends(get_session),
    _: Usuario = Depends(require_admin),
):
    clientes = db.exec(select(Cliente)).all()
    return [{"id": c.id, "nombre_empresa": c.nombre_empresa} for c in clientes]


# =============================================================================
# HU01 - SEED: Crear admin inicial si no existe (util para primer arranque)
# =============================================================================
@app.post("/api/v1/auth/seed-admin", summary="HU01: Crear admin inicial (solo si no hay usuarios)")
def seed_admin(db: Session = Depends(get_session)):
    if db.exec(select(Usuario)).first():
        raise HTTPException(status_code=400, detail="Ya existen usuarios en el sistema")
    admin = Usuario(
        email="admin@colektia.com",
        password_hash=hash_password("Admin1234!"),
        nombre="Administrador",
        rol=RolUsuario.admin,
    )
    db.add(admin)
    db.commit()
    return {"mensaje": "Admin creado", "email": "admin@colektia.com", "password": "Admin1234!"}
