"""
seed_guiones.py — Carga los 6 guiones reales de Colektia en la BD
Actualiza los campos de Cliente (usados por la IA) y carga GuionCliente.

Clientes que coinciden con llamadas ya cargadas:
  - Access Finance  (Mexico)   — Vigente
  - Rapicredit      (Colombia) — Riesgo bajo | Preventiva | Riesgo medio-alto
  - Sistecredito    (Colombia) — Tramo 1-3   | Tramo >3

Uso: python seed_guiones.py
"""

import sys
sys.path.insert(0, ".")

from sqlmodel import Session, select
from database import engine
from models import Cliente, GuionCliente

# =============================================================================
# GUIONES EXTRAIDOS DEL ARCHIVO GUIONES.XLSX
# =============================================================================

GUIONES = [

    # ── 1. ACCESS FINANCE — Vigente (0-30 dias mora) ─────────────────────────
    {
        "cliente_nombre": "Access Finance",
        "script_nombre":  "Access Finance - Vigente",
        "pais":           "Mexico",
        "medio_de_pago":  (
            "Transferencia bancaria (SPEI) usando la CLAVE que aparece en la "
            "seccion 'Pagar tarjeta' en la app. "
            "Establecimientos autorizados mostrando el codigo de pago de la app."
        ),
        "guion_identificacion": (
            "Buenas tardes / dias. Te llamo de tarjeta de credito Yazt. "
            "¿Hablo con [nombre titular]?"
        ),
        "guion_saludo": (
            "Hola [nombre titular], soy [nombre agente], tu asistente virtual de Colektia, "
            "aliados de Access Finance. Esta llamada esta siendo grabada."
        ),
        "guion_entrega_mensaje": (
            "El motivo de mi llamada es porque tienes un saldo pendiente de [valor cuota]. "
            "¿En que fecha podrias realizar el pago para regularizar tu cuenta y evitar recargos?"
        ),
        "guion_negociacion": (
            "¿Me puedes contar que ha hecho que no hayas podido ponerte al dia con el pago? "
            "Quiero entender mejor tu situacion. "
            "Regularizando esta deuda evitaras recargos adicionales y complicaciones futuras. "
            "¿Crees que podrias resolverlo hoy, manana o pasado manana? "
            "Si no puedes pagar el total, podemos registrar al menos el pago minimo. "
            "Plazo maximo para pagar: 5 dias."
        ),
        "guion_agenda_compromiso": (
            "Perfecto. Para registrarlo correctamente: ¿confirmas que vas a realizar el pago "
            "el [fecha acordada]? Perfecto, su compromiso quedo registrado. "
            "Recuerda que mientras mas tiempo dejes sin pagar, mas intereses puedes acumular. "
            "Te recomiendo realizar el pago lo antes posible."
        ),
        "guion_cierre": (
            "Gracias por tu compromiso. Que tengas buen dia."
        ),
        "reglas_adicionales": (
            "SEVERIDADES (fallo critico si ocurre):\n"
            "- No usar el termino 'humano' ni ofrecer transferencias si no esta previsto.\n"
            "- No mencionar que se enviaran detalles de pago por WhatsApp.\n"
            "- No entregar informacion a terceros.\n"
            "- No identificarse al inicio de la llamada.\n"
            "- No mencionar la palabra 'deuda' (usar 'saldo pendiente' o 'cuota vencida').\n\n"
            "ADICIONALES:\n"
            "Si el cliente pide hablar con un agente: 'En estos momentos los especialistas "
            "se encuentran ocupados, lo llamaremos mas tarde.'\n"
            "Si el cliente dice que esta desempleado: 'Entendemos tu situacion, un especialista "
            "lo contactara luego.'\n"
            "Canal de atencion: 55 4161 6550."
        ),
    },

    # ── 2. RAPICREDIT — Riesgo Bajo / Novacion Mora (mora alta, >60 dias) ────
    {
        "cliente_nombre": "Rapicredit",
        "script_nombre":  "Rapicredit - Riesgo Bajo / Novacion Mora",
        "pais":           "Colombia",
        "medio_de_pago":  (
            "PSE (Pago Seguro Electronico) | Banco Davivienda | "
            "Bancolombia (sucursal, corresponsales o Sucursal Virtual) | "
            "Efecty | Nequi | SuSuerte (solo Caldas)."
        ),
        "guion_identificacion": (
            "¿Hablo con [nombre titular]?"
        ),
        "guion_saludo": (
            "Hola [nombre titular], habla [nombre agente], agente AI de Rapicredit. "
            "Le informo que esta llamada esta siendo grabada y monitoreada para fines de calidad."
        ),
        "guion_entrega_mensaje": (
            "Desde Rapicredit, estamos para apoyarlo con alternativas que le permitan "
            "normalizar sus obligaciones y mejorar su situacion financiera. "
            "Actualmente dispone de un saldo de [valor cuota], con [dias moratorios] dias de mora. "
            "¿Le parece si revisamos opciones?"
        ),
        "guion_negociacion": (
            "Como referencia, su saldo total hoy es [valor deuda total]. "
            "Podemos avanzar con una novacion: creamos un credito nuevo que reemplaza al anterior "
            "para que empiece de cero y la mora no siga creciendo. "
            "El valor de la novacion es [valor cuota novacion]. ¿Le parece si avanzamos? "
            "¿Confirma que acepta la novacion por [valor acordado]? "
            "¿Que fecha dentro de los proximos 5 dias le parece para hacer ese compromiso?"
        ),
        "guion_agenda_compromiso": (
            "Confirmo que tenemos un compromiso de pago por [valor acordado] para el [fecha acordada]. "
            "Muchas gracias por su compromiso. "
            "Para completar la novacion, entre a rapicredit.com, inicie sesion y vaya a "
            "creditos activos en 'Ampliar Plazo'. "
            "Si paga por Nequi, Daviplata, consignacion bancaria o Sucursal Virtual Bancolombia, "
            "recuerde enviar el comprobante a ayuda@rapicredit.com o al WhatsApp 3124498392."
        ),
        "guion_cierre": (
            "Ya quedo registrado su compromiso por la novacion para el [fecha acordada]. "
            "Gracias por su compromiso, buen dia."
        ),
        "reglas_adicionales": (
            "SEVERIDADES (fallo critico si ocurre):\n"
            "- Entregar informacion a un tercero (no titular).\n"
            "- No identificarse al inicio de la llamada.\n"
            "- Mencionar la palabra 'deuda' (usar 'saldo', 'obligacion' o 'cuota').\n\n"
            "TONO REQUERIDO:\n"
            "- Empatico y cercano, como asesor de Rapicredit.\n"
            "- Profesional y claro, sin tecnicismos.\n"
            "- Adaptado al publico colombiano.\n"
            "- Respetuoso y sin presiones.\n"
            "Canales de atencion: Servicio al cliente 6013902670 | Linea cartera 6017448202."
        ),
    },

    # ── 3. RAPICREDIT — Preventiva (mora 0, antes del vencimiento) ───────────
    {
        "cliente_nombre": "Rapicredit",
        "script_nombre":  "Rapicredit - Preventiva / Novacion Preventiva",
        "pais":           "Colombia",
        "medio_de_pago":  (
            "PSE (Pago Seguro Electronico) | Banco Davivienda | "
            "Bancolombia (sucursal, corresponsales o Sucursal Virtual) | "
            "Efecty | Nequi | SuSuerte (solo Caldas)."
        ),
        "guion_identificacion": "¿Hablo con [nombre titular]?",
        "guion_saludo": (
            "Hola [nombre titular], habla [nombre agente] de Rapicredit. "
            "Le informo que esta llamada esta siendo grabada y monitoreada para fines de calidad."
        ),
        "guion_entrega_mensaje": (
            "Desde Rapicredit, estamos para apoyarlo con alternativas que le permitan "
            "normalizar sus obligaciones y mejorar su situacion financiera. "
            "Actualmente dispone de un saldo de [valor cuota], con fecha de vencimiento "
            "el dia [fecha vencimiento]. ¿Le parece si revisamos opciones?"
        ),
        "guion_negociacion": (
            "Su saldo total hoy es [valor cuota]. Podemos avanzar con una novacion preventiva: "
            "creamos un credito nuevo antes de que entre en mora para que evite cobros adicionales. "
            "¿Le parece si avanzamos? ¿Confirma que acepta la novacion por [valor acordado]? "
            "¿Que fecha dentro de los proximos 6 dias le parece para hacer ese compromiso?"
        ),
        "guion_agenda_compromiso": (
            "Queda confirmado un pago de [valor novacion] para [fecha acordada]. "
            "Muchas gracias por su compromiso. "
            "Para completar la novacion, entre a rapicredit.com > creditos activos > 'Ampliar Plazo'. "
            "Recuerde enviarnos el comprobante a ayuda@rapicredit.com o al WhatsApp 3124498392."
        ),
        "guion_cierre": (
            "Ya quedo registrado su compromiso por la novacion para el [fecha acordada]. "
            "Gracias por su compromiso, buen dia."
        ),
        "reglas_adicionales": (
            "SEVERIDADES (fallo critico si ocurre):\n"
            "- Entregar informacion a un tercero.\n"
            "- No identificarse al inicio de la llamada.\n"
            "- Mencionar la palabra 'deuda'.\n\n"
            "TONO: Empatico, cercano, profesional, sin presiones. "
            "Canales: 6013902670 | 6017448202."
        ),
    },

    # ── 4. RAPICREDIT — Riesgo Medio-Alto (mora 31-90 dias) ─────────────────
    {
        "cliente_nombre": "Rapicredit",
        "script_nombre":  "Rapicredit - Riesgo Medio Alto",
        "pais":           "Colombia",
        "medio_de_pago":  (
            "PSE | Banco Davivienda | Bancolombia | Efecty | Nequi | SuSuerte (solo Caldas)."
        ),
        "guion_identificacion": "¿Hablo con [nombre titular]?",
        "guion_saludo": (
            "Hola [nombre titular], habla [nombre agente] de Rapicredit. "
            "Esta llamada esta siendo grabada para fines de calidad."
        ),
        "guion_entrega_mensaje": (
            "Le contactamos desde Rapicredit porque tiene una obligacion pendiente de [valor cuota] "
            "con [dias moratorios] dias de mora. Es importante que regularice su situacion "
            "para evitar que los intereses sigan aumentando y afecten su historial crediticio."
        ),
        "guion_negociacion": (
            "Entendemos que pueden haber situaciones que dificulten el pago. "
            "¿Podria contarnos que ha pasado? "
            "Tenemos opciones de refinanciamiento que podrian ajustarse a su situacion. "
            "¿Podria comprometerse con un pago parcial en los proximos dias? "
            "Cualquier abono detiene el crecimiento de intereses."
        ),
        "guion_agenda_compromiso": (
            "Muy bien, queda registrado su compromiso de pago por [valor acordado] "
            "para el [fecha acordada]. "
            "Recuerde que pagar a tiempo protege su historial financiero."
        ),
        "guion_cierre": (
            "Gracias por su atencion y compromiso. Buen dia."
        ),
        "reglas_adicionales": (
            "SEVERIDADES (fallo critico si ocurre):\n"
            "- Entregar informacion a un tercero.\n"
            "- No identificarse al inicio de la llamada.\n"
            "- Mencionar la palabra 'deuda'.\n\n"
            "TONO: Empatico, firme pero respetuoso, sin presiones. "
            "Canales: 6013902670 | 6017448202."
        ),
    },

    # ── 5. SISTECREDITO — Tramo 1 a 3 cuotas vencidas (mora 1-30 dias) ──────
    {
        "cliente_nombre": "Sistecredito",
        "script_nombre":  "Sistecredito - Tramo 1 a 3 cuotas",
        "pais":           "Colombia",
        "medio_de_pago":  (
            "Efecty codigo 112901 | Gana codigo 441 | "
            "PSE (Bancolombia, Nequi u otros bancos habilitados) | "
            "Portal web: payonline-web.sistecredito.com | "
            "WhatsApp Sistecredito: 3208899898."
        ),
        "guion_identificacion": (
            "Buenas tardes / dias, te habla [nombre agente], asesor de Sistecredito. "
            "¿Hablo con [nombre titular]?"
        ),
        "guion_saludo": (
            "Espero que se encuentre bien. "
            "Le informamos que esta llamada esta siendo grabada para garantizar la calidad "
            "de nuestro servicio."
        ),
        "guion_entrega_mensaje": (
            "El motivo de mi llamada es para recordarle que actualmente tiene un saldo "
            "pendiente de [valor cuota] por su credito en [establecimiento de compra], "
            "con [numero dias moratorios] dias de mora y [numero cuotas vencidas] cuota(s) vencida(s). "
            "Los intereses por mora seguiran aumentando si no se regulariza pronto."
        ),
        "guion_negociacion": (
            "Recuerde que los intereses son diarios y el saldo puede cambiar. "
            "Pagar antes le ahorra ese costo adicional. "
            "¿Podria resolverlo hoy, manana o pasado manana? "
            "¿Prefiere hacer un abono parcial minimo de [valor pago minimo] para el dia [fecha]? "
            "Plazo maximo disponible: 30 dias."
        ),
        "guion_agenda_compromiso": (
            "Perfecto, confirmamos el valor a pagar de [valor cuota] pesos para [fecha acordada]. "
            "¿De acuerdo? ¿Ya conoce los canales oficiales de pago disponibles? "
            "Tambien puede pagar en el almacen donde realizo la compra."
        ),
        "guion_cierre": (
            "[Nombre titular], gracias por su atencion. "
            "Recuerde que hablo con [nombre agente] de Sistecredito."
        ),
        "reglas_adicionales": (
            "SEVERIDADES (fallo critico si ocurre):\n"
            "- Entregar informacion a un tercero sin autorizacion.\n"
            "- No identificarse como asesor de Sistecredito al inicio.\n"
            "- Amenazar al cliente o usar lenguaje coercitivo.\n"
            "- No informar el monto exacto de la deuda cuando se solicita.\n\n"
            "Portal de pago: payonline-web.sistecredito.com\n"
            "WhatsApp: 3208899898."
        ),
    },

    # ── 6. SISTECREDITO — Tramo >3 cuotas vencidas (mora >30 dias) ──────────
    {
        "cliente_nombre": "Sistecredito",
        "script_nombre":  "Sistecredito - Tramo mas de 3 cuotas",
        "pais":           "Colombia",
        "medio_de_pago":  (
            "Efecty codigo 112901 | Gana codigo 441 | "
            "PSE (Bancolombia, Nequi u otros bancos habilitados) | "
            "Portal web: payonline-web.sistecredito.com | "
            "WhatsApp Sistecredito: 3208899898."
        ),
        "guion_identificacion": (
            "Buenas tardes / dias, te habla [nombre agente], asesor de Sistecredito. "
            "¿Hablo con [nombre titular]?"
        ),
        "guion_saludo": (
            "Espero que se encuentre bien. "
            "Le informamos que esta llamada esta siendo grabada para garantizar la calidad "
            "de nuestro servicio."
        ),
        "guion_entrega_mensaje": (
            "El motivo de mi llamada es para recordarle que actualmente tiene un saldo "
            "pendiente de [valor cuota] a dia de hoy por su credito en [establecimiento], "
            "con [numero dias moratorios] dias de mora y [numero cuotas vencidas] cuota(s) vencida(s). "
            "Los intereses por mora seguiran aumentando."
        ),
        "guion_negociacion": (
            "Recuerde que los intereses son diarios y el saldo puede cambiar: "
            "pagar antes le ahorra ese costo adicional. "
            "¿Podria resolverlo hoy, manana o pasado manana? "
            "Comprendo que se le dificulte pagar en los proximos dias. "
            "¿Podria resolverlo dentro de los proximos 30 dias? "
            "Asi evitaria que los intereses sigan aumentando durante semanas. "
            "¿Prefiere hacer un abono parcial minimo de [valor pago minimo]?"
        ),
        "guion_agenda_compromiso": (
            "Perfecto, le informamos que los intereses por mora incrementan de manera diaria. "
            "Confirmamos el valor a pagar de [valor cuota] pesos para [fecha acordada]. "
            "¿De acuerdo? ¿Ya conoce los canales oficiales de pago? "
            "Tambien puede pagar en el almacen donde realizo la compra."
        ),
        "guion_cierre": (
            "[Nombre titular], gracias por su atencion. "
            "Recuerde que hablo con [nombre agente] de Sistecredito."
        ),
        "reglas_adicionales": (
            "SEVERIDADES (fallo critico si ocurre):\n"
            "- Entregar informacion a un tercero sin autorizacion.\n"
            "- No identificarse como asesor de Sistecredito al inicio.\n"
            "- Amenazar al cliente o usar lenguaje coercitivo.\n"
            "- No informar el monto cuando se solicita.\n\n"
            "Portal: payonline-web.sistecredito.com | WhatsApp: 3208899898."
        ),
    },
]


# =============================================================================
# CARGA EN BASE DE DATOS
# =============================================================================

def main():
    print("Cargando 6 guiones en la base de datos...\n")

    with Session(engine) as db:

        for g in GUIONES:
            nombre_cliente = g["cliente_nombre"]

            # 1. Actualizar el Cliente con el guion principal
            #    (usamos el ultimo guion de cada cliente como el vigente en Cliente)
            cliente = db.exec(
                select(Cliente).where(Cliente.nombre_empresa == nombre_cliente)
            ).first()

            if cliente:
                cliente.pais                     = g["pais"]
                cliente.medio_de_pago            = g["medio_de_pago"]
                cliente.guion_identificacion     = g["guion_identificacion"]
                cliente.guion_saludo             = g["guion_saludo"]
                cliente.guion_entrega_mensaje    = g["guion_entrega_mensaje"]
                cliente.guion_negociacion        = g["guion_negociacion"]
                cliente.guion_agenda_compromiso  = g["guion_agenda_compromiso"]
                cliente.guion_cierre             = g["guion_cierre"]
                cliente.reglas_adicionales       = g["reglas_adicionales"]
                db.add(cliente)
                print(f"  ACTUALIZADO  Cliente '{nombre_cliente}' con guion principal")
            else:
                print(f"  OMITIDO      Cliente '{nombre_cliente}' no existe en BD — carga primero las llamadas")

            # 2. Guardar en GuionCliente (historico completo de scripts)
            guion_completo = (
                f"=== IDENTIFICACION ===\n{g['guion_identificacion']}\n\n"
                f"=== SALUDO ===\n{g['guion_saludo']}\n\n"
                f"=== ENTREGA DE MENSAJE ===\n{g['guion_entrega_mensaje']}\n\n"
                f"=== NEGOCIACION ===\n{g['guion_negociacion']}\n\n"
                f"=== AGENDA DE COMPROMISO ===\n{g['guion_agenda_compromiso']}\n\n"
                f"=== CIERRE ===\n{g['guion_cierre']}\n\n"
                f"=== REGLAS Y SEVERIDADES ===\n{g['reglas_adicionales']}\n\n"
                f"=== MEDIO DE PAGO ===\n{g['medio_de_pago']}"
            )

            # Verificar si ya existe este guion
            existente = db.exec(
                select(GuionCliente).where(GuionCliente.nombre == g["script_nombre"])
            ).first()

            if existente:
                existente.guion_auditoria = guion_completo
                db.add(existente)
                print(f"  ACTUALIZADO  GuionCliente '{g['script_nombre']}'")
            else:
                nuevo_guion = GuionCliente(
                    nombre=g["script_nombre"],
                    guion_auditoria=guion_completo,
                )
                db.add(nuevo_guion)
                print(f"  CREADO       GuionCliente '{g['script_nombre']}'")

        db.commit()

    print("\nGuiones cargados exitosamente.")
    print("La IA usara los guiones de cada cliente en las proximas auditorias.")
    print("\nPara re-auditar las llamadas existentes con los guiones nuevos:")
    print("  POST http://localhost:8000/api/v1/auditoria/ejecutar")
    print("  (Primero borra las evaluaciones existentes desde reset_db.py si quieres empezar limpio)")


if __name__ == "__main__":
    main()
