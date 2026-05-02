"""
seed_rubricas.py — Carga rúbricas y criterios reales por empresa y rango de mora.
Basadas en los guiones oficiales de Colektia cargados en seed_guiones.py.

Rúbricas creadas:
  - Access Finance  : Vigente (0-30 días)
  - Rapicredit      : Riesgo Bajo/Novación (mora ≥ 60 días)
  - Rapicredit      : Riesgo Medio-Alto (31-90 días)
  - Sistecredito    : Tramo 1-3 cuotas (1-30 días mora)
  - Sistecredito    : Tramo >3 cuotas (>30 días mora)

Uso: python seed_rubricas.py  (con venv activado)
"""

import sys
sys.path.insert(0, ".")

from sqlmodel import Session, select
from database import engine
from models import Rubrica, Criterio

# =============================================================================
# DEFINICIÓN DE RÚBRICAS
# =============================================================================
# Cada criterio tiene:
#   nombre       : Etiqueta corta para el dashboard
#   descripcion  : Lo que la IA debe buscar en la transcripción
#   peso         : 1 (normal) | 2 (importante) | 3 (crítico)
#   es_severidad : True = fallo crítico (no suma puntos, pero activa error_critico)

RUBRICAS = [

    # ──────────────────────────────────────────────────────────────────────────
    # 1. ACCESS FINANCE — Vigente (0-30 días mora)
    # ──────────────────────────────────────────────────────────────────────────
    {
        "nombre":   "Access Finance - Vigente",
        "empresa":  "Access Finance",
        "mora_min": 0,
        "mora_max": 30,
        "criterios": [
            {
                "nombre": "Identificación del agente",
                "descripcion": (
                    "El agente se identifica correctamente al inicio indicando su nombre "
                    "y que llama de parte de la tarjeta de crédito Yazt / Access Finance. "
                    "Fallo si no se presenta."
                ),
                "peso": 2,
                "es_severidad": True,
            },
            {
                "nombre": "Verificación del titular",
                "descripcion": (
                    "El agente confirma que habla con el titular de la cuenta antes de "
                    "entregar cualquier información del crédito."
                ),
                "peso": 2,
                "es_severidad": True,
            },
            {
                "nombre": "Aviso de grabación",
                "descripcion": (
                    "El agente informa al cliente que la llamada está siendo grabada."
                ),
                "peso": 1,
                "es_severidad": False,
            },
            {
                "nombre": "Entrega del saldo pendiente",
                "descripcion": (
                    "El agente comunica el saldo pendiente o valor de cuota de manera clara, "
                    "usando términos como 'saldo pendiente' o 'cuota vencida'. "
                    "NO debe usar la palabra 'deuda'."
                ),
                "peso": 2,
                "es_severidad": False,
            },
            {
                "nombre": "No usa la palabra 'deuda'",
                "descripcion": (
                    "El agente NUNCA usa la palabra 'deuda'. Debe sustituirla por "
                    "'saldo pendiente', 'cuota vencida' o equivalente. "
                    "Fallo crítico si la usa."
                ),
                "peso": 1,
                "es_severidad": True,
            },
            {
                "nombre": "Exploración / Negociación",
                "descripcion": (
                    "El agente pregunta al cliente la razón del no pago o explora "
                    "cuándo puede realizar el pago (hoy, mañana, pasado mañana). "
                    "No debe presionar más allá del plazo máximo de 5 días."
                ),
                "peso": 2,
                "es_severidad": False,
            },
            {
                "nombre": "Registro del compromiso",
                "descripcion": (
                    "Si el cliente acepta pagar, el agente confirma verbalmente la fecha "
                    "y el monto del compromiso y lo da por registrado."
                ),
                "peso": 2,
                "es_severidad": False,
            },
            {
                "nombre": "Cierre cordial",
                "descripcion": (
                    "El agente cierra la llamada de forma amable, agradeciendo al cliente "
                    "y deseándole un buen día."
                ),
                "peso": 1,
                "es_severidad": False,
            },
            {
                "nombre": "No amenaza ni presiona al cliente",
                "descripcion": (
                    "El agente no usa lenguaje coercitivo, amenazas ni presión excesiva. "
                    "El tono debe ser empático y respetuoso en todo momento. "
                    "Fallo crítico si usa amenazas."
                ),
                "peso": 2,
                "es_severidad": True,
            },
        ],
    },

    # ──────────────────────────────────────────────────────────────────────────
    # 2. RAPICREDIT — Riesgo Bajo / Novación Mora (mora ≥ 60 días)
    # ──────────────────────────────────────────────────────────────────────────
    {
        "nombre":   "Rapicredit - Riesgo Bajo / Novación",
        "empresa":  "Rapicredit",
        "mora_min": 60,
        "mora_max": 9999,
        "criterios": [
            {
                "nombre": "Identificación del agente",
                "descripcion": (
                    "El agente se identifica por nombre e indica que llama de Rapicredit "
                    "al inicio de la llamada. Fallo crítico si no lo hace."
                ),
                "peso": 2,
                "es_severidad": True,
            },
            {
                "nombre": "Verificación del titular",
                "descripcion": (
                    "El agente confirma que habla con el titular antes de entregar "
                    "información del crédito. No entrega datos a terceros."
                ),
                "peso": 2,
                "es_severidad": True,
            },
            {
                "nombre": "Aviso de grabación y monitoreo",
                "descripcion": (
                    "El agente informa que la llamada es grabada y monitoreada para "
                    "fines de calidad."
                ),
                "peso": 1,
                "es_severidad": False,
            },
            {
                "nombre": "Presentación de alternativas (novación)",
                "descripcion": (
                    "El agente presenta la opción de novación como solución: explica "
                    "que se crea un crédito nuevo que reemplaza al anterior para que "
                    "el cliente empiece de cero y la mora no siga creciendo."
                ),
                "peso": 3,
                "es_severidad": False,
            },
            {
                "nombre": "Comunica saldo y días de mora",
                "descripcion": (
                    "El agente informa el saldo actual y los días de mora de forma "
                    "clara. No debe usar la palabra 'deuda'."
                ),
                "peso": 2,
                "es_severidad": False,
            },
            {
                "nombre": "No usa la palabra 'deuda'",
                "descripcion": (
                    "El agente NUNCA usa la palabra 'deuda'. Debe usar 'saldo', "
                    "'obligación' o 'cuota'. Fallo crítico si la usa."
                ),
                "peso": 1,
                "es_severidad": True,
            },
            {
                "nombre": "Confirmación del compromiso",
                "descripcion": (
                    "Si el cliente acepta la novación o cualquier pago, el agente "
                    "confirma el monto y fecha acordados y los registra."
                ),
                "peso": 2,
                "es_severidad": False,
            },
            {
                "nombre": "Informa canales de pago y comprobante",
                "descripcion": (
                    "El agente indica los canales de pago habilitados (PSE, Efecty, "
                    "Nequi, Bancolombia, etc.) y cómo enviar el comprobante."
                ),
                "peso": 2,
                "es_severidad": False,
            },
            {
                "nombre": "Tono empático y sin presiones",
                "descripcion": (
                    "El agente mantiene un tono empático, profesional y sin presiones "
                    "durante toda la llamada. Fallo crítico si amenaza al cliente."
                ),
                "peso": 2,
                "es_severidad": True,
            },
            {
                "nombre": "Cierre cordial",
                "descripcion": (
                    "El agente cierra la llamada agradeciendo y deseando un buen día."
                ),
                "peso": 1,
                "es_severidad": False,
            },
        ],
    },

    # ──────────────────────────────────────────────────────────────────────────
    # 3. RAPICREDIT — Riesgo Medio-Alto (31-59 días mora)
    # ──────────────────────────────────────────────────────────────────────────
    {
        "nombre":   "Rapicredit - Riesgo Medio Alto",
        "empresa":  "Rapicredit",
        "mora_min": 31,
        "mora_max": 59,
        "criterios": [
            {
                "nombre": "Identificación del agente",
                "descripcion": (
                    "El agente se identifica por nombre e indica que llama de Rapicredit. "
                    "Fallo crítico si no lo hace."
                ),
                "peso": 2,
                "es_severidad": True,
            },
            {
                "nombre": "Verificación del titular",
                "descripcion": (
                    "El agente confirma que habla con el titular antes de entregar "
                    "información. No entrega datos a terceros."
                ),
                "peso": 2,
                "es_severidad": True,
            },
            {
                "nombre": "Aviso de grabación",
                "descripcion": "El agente informa que la llamada está siendo grabada.",
                "peso": 1,
                "es_severidad": False,
            },
            {
                "nombre": "Comunica obligación pendiente y días de mora",
                "descripcion": (
                    "El agente informa el valor de la obligación pendiente y los días "
                    "de mora, destacando el riesgo de que los intereses sigan aumentando."
                ),
                "peso": 2,
                "es_severidad": False,
            },
            {
                "nombre": "No usa la palabra 'deuda'",
                "descripcion": (
                    "El agente NUNCA usa la palabra 'deuda'. Debe usar 'obligación', "
                    "'saldo' o 'cuota'. Fallo crítico si la usa."
                ),
                "peso": 1,
                "es_severidad": True,
            },
            {
                "nombre": "Exploración empática de la situación",
                "descripcion": (
                    "El agente pregunta al cliente qué ha dificultado el pago y escucha "
                    "la respuesta antes de proponer opciones de refinanciamiento."
                ),
                "peso": 2,
                "es_severidad": False,
            },
            {
                "nombre": "Propone opciones de pago/refinanciamiento",
                "descripcion": (
                    "El agente menciona que existen opciones de refinanciamiento o pagos "
                    "parciales para ajustarse a la situación del cliente."
                ),
                "peso": 2,
                "es_severidad": False,
            },
            {
                "nombre": "Registro del compromiso",
                "descripcion": (
                    "Si el cliente acepta un pago, el agente confirma monto y fecha "
                    "y lo registra verbalmente."
                ),
                "peso": 2,
                "es_severidad": False,
            },
            {
                "nombre": "Tono empático, firme y sin amenazas",
                "descripcion": (
                    "El agente es firme pero respetuoso. No usa lenguaje amenazante "
                    "ni coercitivo. Fallo crítico si amenaza al cliente."
                ),
                "peso": 2,
                "es_severidad": True,
            },
            {
                "nombre": "Cierre cordial",
                "descripcion": (
                    "El agente cierra la llamada de forma amable."
                ),
                "peso": 1,
                "es_severidad": False,
            },
        ],
    },

    # ──────────────────────────────────────────────────────────────────────────
    # 4. SISTECREDITO — Tramo 1 a 3 cuotas (mora 1-30 días)
    # ──────────────────────────────────────────────────────────────────────────
    {
        "nombre":   "Sistecredito - Tramo 1 a 3 cuotas",
        "empresa":  "Sistecredito",
        "mora_min": 1,
        "mora_max": 30,
        "criterios": [
            {
                "nombre": "Identificación como asesor de Sistecredito",
                "descripcion": (
                    "El agente se identifica por nombre e indica que llama de "
                    "Sistecredito al inicio de la llamada. Fallo crítico si no lo hace."
                ),
                "peso": 2,
                "es_severidad": True,
            },
            {
                "nombre": "Verificación del titular",
                "descripcion": (
                    "El agente confirma que habla con el titular antes de entregar "
                    "información del crédito. No entrega datos a terceros."
                ),
                "peso": 2,
                "es_severidad": True,
            },
            {
                "nombre": "Aviso de grabación",
                "descripcion": (
                    "El agente informa que la llamada está siendo grabada para "
                    "garantizar la calidad del servicio."
                ),
                "peso": 1,
                "es_severidad": False,
            },
            {
                "nombre": "Informa saldo, mora y cuotas vencidas",
                "descripcion": (
                    "El agente comunica claramente el saldo pendiente, los días de mora "
                    "y el número de cuotas vencidas, mencionando que los intereses son diarios."
                ),
                "peso": 2,
                "es_severidad": False,
            },
            {
                "nombre": "No amenaza ni usa lenguaje coercitivo",
                "descripcion": (
                    "El agente no usa amenazas ni lenguaje intimidatorio. "
                    "Fallo crítico si amenaza al cliente."
                ),
                "peso": 2,
                "es_severidad": True,
            },
            {
                "nombre": "Propone fechas de pago (hoy/mañana/pasado)",
                "descripcion": (
                    "El agente pregunta si el cliente puede pagar hoy, mañana o pasado "
                    "mañana, sin presionar más allá del plazo máximo de 30 días."
                ),
                "peso": 2,
                "es_severidad": False,
            },
            {
                "nombre": "Ofrece pago parcial (abono mínimo)",
                "descripcion": (
                    "Si el cliente no puede pagar el total, el agente ofrece la opción "
                    "de realizar un abono parcial mínimo."
                ),
                "peso": 1,
                "es_severidad": False,
            },
            {
                "nombre": "Confirmación del compromiso de pago",
                "descripcion": (
                    "El agente confirma el monto y fecha de pago acordados verbalmente "
                    "y los registra."
                ),
                "peso": 2,
                "es_severidad": False,
            },
            {
                "nombre": "Informa canales de pago oficiales",
                "descripcion": (
                    "El agente menciona al menos un canal oficial de pago: Efecty "
                    "(código 112901), Gana (código 441), PSE, portal web o WhatsApp 3208899898."
                ),
                "peso": 1,
                "es_severidad": False,
            },
            {
                "nombre": "Cierre con identificación del asesor",
                "descripcion": (
                    "El agente cierra la llamada agradeciéndole al cliente y recordándole "
                    "su nombre y que habló con Sistecredito."
                ),
                "peso": 1,
                "es_severidad": False,
            },
        ],
    },

    # ──────────────────────────────────────────────────────────────────────────
    # 5. SISTECREDITO — Tramo >3 cuotas (mora > 30 días)
    # ──────────────────────────────────────────────────────────────────────────
    {
        "nombre":   "Sistecredito - Tramo más de 3 cuotas",
        "empresa":  "Sistecredito",
        "mora_min": 31,
        "mora_max": 9999,
        "criterios": [
            {
                "nombre": "Identificación como asesor de Sistecredito",
                "descripcion": (
                    "El agente se identifica por nombre e indica que llama de "
                    "Sistecredito al inicio. Fallo crítico si no lo hace."
                ),
                "peso": 2,
                "es_severidad": True,
            },
            {
                "nombre": "Verificación del titular",
                "descripcion": (
                    "El agente confirma que habla con el titular antes de entregar "
                    "información del crédito. No entrega datos a terceros."
                ),
                "peso": 2,
                "es_severidad": True,
            },
            {
                "nombre": "Aviso de grabación",
                "descripcion": (
                    "El agente informa que la llamada está siendo grabada."
                ),
                "peso": 1,
                "es_severidad": False,
            },
            {
                "nombre": "Informa saldo, mora y cuotas vencidas",
                "descripcion": (
                    "El agente comunica el saldo pendiente, días de mora y cuotas "
                    "vencidas, destacando que los intereses aumentan diariamente."
                ),
                "peso": 2,
                "es_severidad": False,
            },
            {
                "nombre": "No amenaza ni usa lenguaje coercitivo",
                "descripcion": (
                    "El agente no usa amenazas ni lenguaje intimidatorio. "
                    "Fallo crítico si amenaza al cliente."
                ),
                "peso": 2,
                "es_severidad": True,
            },
            {
                "nombre": "Exploración de capacidad de pago",
                "descripcion": (
                    "El agente explora la capacidad de pago del cliente: propone "
                    "pagar hoy, mañana, pasado mañana o dentro de 30 días para "
                    "frenar el crecimiento de intereses."
                ),
                "peso": 2,
                "es_severidad": False,
            },
            {
                "nombre": "Ofrece abono parcial mínimo",
                "descripcion": (
                    "Si el cliente no puede pagar el total, el agente ofrece la opción "
                    "de un abono parcial mínimo con monto específico."
                ),
                "peso": 1,
                "es_severidad": False,
            },
            {
                "nombre": "Confirmación del compromiso de pago",
                "descripcion": (
                    "El agente confirma monto y fecha de pago acordados verbalmente, "
                    "recordando que los intereses siguen incrementando diariamente."
                ),
                "peso": 2,
                "es_severidad": False,
            },
            {
                "nombre": "Informa canales de pago oficiales",
                "descripcion": (
                    "El agente menciona al menos un canal oficial de pago: Efecty, "
                    "Gana, PSE, portal web payonline-web.sistecredito.com o WhatsApp."
                ),
                "peso": 1,
                "es_severidad": False,
            },
            {
                "nombre": "Cierre con identificación del asesor",
                "descripcion": (
                    "El agente cierra la llamada agradeciendo y recordando su nombre "
                    "y que habló con Sistecredito."
                ),
                "peso": 1,
                "es_severidad": False,
            },
        ],
    },
]


# =============================================================================
# CARGA EN BASE DE DATOS
# =============================================================================

def main():
    print("Cargando rúbricas y criterios en la base de datos...\n")
    total_rubricas  = 0
    total_criterios = 0

    with Session(engine) as db:
        for r in RUBRICAS:
            # Verificar si ya existe esta rúbrica (por nombre)
            existente = db.exec(
                select(Rubrica).where(Rubrica.nombre == r["nombre"])
            ).first()

            if existente:
                # Actualizar campos básicos
                existente.empresa  = r["empresa"]
                existente.mora_min = r["mora_min"]
                existente.mora_max = r["mora_max"]
                existente.activo   = True
                rubrica = existente
                db.add(rubrica)
                db.flush()  # Para obtener el id si es nuevo

                # Eliminar criterios existentes para reemplazarlos
                criterios_existentes = db.exec(
                    select(Criterio).where(Criterio.rubrica_id == rubrica.id)
                ).all()
                for c in criterios_existentes:
                    db.delete(c)
                db.flush()
                print(f"  ACTUALIZADO  Rúbrica '{r['nombre']}' (empresa: {r['empresa']}, mora {r['mora_min']}-{r['mora_max']} días)")
            else:
                rubrica = Rubrica(
                    nombre   = r["nombre"],
                    empresa  = r["empresa"],
                    mora_min = r["mora_min"],
                    mora_max = r["mora_max"],
                    activo   = True,
                )
                db.add(rubrica)
                db.flush()  # Necesitamos el id antes de crear criterios
                print(f"  CREADO       Rúbrica '{r['nombre']}' (empresa: {r['empresa']}, mora {r['mora_min']}-{r['mora_max']} días)")

            total_rubricas += 1

            # Cargar criterios
            for c in r["criterios"]:
                criterio = Criterio(
                    nombre       = c["nombre"],
                    descripcion  = c["descripcion"],
                    peso         = c["peso"],
                    es_severidad = c["es_severidad"],
                    rubrica_id   = rubrica.id,
                )
                db.add(criterio)
                total_criterios += 1
                tipo = "⚠ SEVERIDAD" if c["es_severidad"] else f"peso {c['peso']}"
                print(f"             + {c['nombre']} ({tipo})")

        db.commit()

    print(f"\n{'─'*60}")
    print(f"  {total_rubricas} rúbricas cargadas | {total_criterios} criterios creados")
    print(f"{'─'*60}")
    print("\nPróximos pasos:")
    print("  1. Ejecuta POST http://localhost:8000/api/v1/auditoria/ejecutar")
    print("     para re-auditar las llamadas existentes con las nuevas rúbricas.")
    print("  2. O espera el ciclo automático de 240 minutos.")
    print("\nNota: si quieres empezar con evaluaciones limpias, borra las existentes")
    print("      en PostgreSQL: DELETE FROM evaluacion;")
    print("      y luego vuelve a ejecutar seed_data.py + auditoria/ejecutar.")


if __name__ == "__main__":
    main()
