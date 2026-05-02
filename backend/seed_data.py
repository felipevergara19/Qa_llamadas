"""
seed_data.py — Carga datos de ejemplo para desarrollo y demos
Uso: python seed_data.py
Requiere que el backend este corriendo en localhost:8000
"""

import requests
import json

BASE_URL = "http://localhost:8000"

LLAMADAS = [
    # ── ACCESS FINANCE — mora baja (0-30 dias) ──────────────────────────────
    {
        "Call_ID": "CALL-AF-001",
        "Empresa": "Access Finance",
        "Estatus": "Comprometido",
        "Cuenta": "CTA-10045",
        "Grabacion": "https://storage.example.com/af-001.mp3",
        "Proveedor": "Colly",
        "createdTime": "2026-04-28T10:15:00",
        "Fecha de vencimiento": "2026-04-15",
        "Días de mora": 13,
        "Saldo vencido": 150000,
        "Saldo facturado": 180000,
        "Saldo total": 180000,
        "Transcrip": (
            "Agent: Buenos dias, le habla Carlos Mendoza de Access Finance. "
            "Necesito hablar con el titular de la cuenta por favor. "
            "Debtor: Si, soy yo. "
            "Agent: Señor, le llamo porque tiene un saldo vencido de $150.000 con fecha de vencimiento el 15 de abril. "
            "Debtor: Si, lo se, he tenido problemas este mes. "
            "Agent: Entiendo su situacion. ¿Podria comprometerse a un pago para esta semana? "
            "Debtor: Si, puedo pagar el viernes 3 de mayo unos $80.000. "
            "Agent: Perfecto, queda registrado su compromiso de pago de $80.000 para el viernes 3 de mayo. "
            "Muchas gracias y que tenga un buen dia. "
            "Debtor: Gracias, hasta luego."
        ),
    },
    {
        "Call_ID": "CALL-AF-002",
        "Empresa": "Access Finance",
        "Estatus": "No contesta",
        "Cuenta": "CTA-10089",
        "Grabacion": "https://storage.example.com/af-002.mp3",
        "Proveedor": "Colly",
        "createdTime": "2026-04-28T11:30:00",
        "Fecha de vencimiento": "2026-04-10",
        "Días de mora": 18,
        "Saldo vencido": 220000,
        "Saldo facturado": 220000,
        "Saldo total": 220000,
        "Transcrip": (
            "Agent: Buenos dias, le habla Maria Lopez de Access Finance, llamo para el titular de la cuenta. "
            "Debtor: ¿Quien es? "
            "Agent: Soy Maria Lopez de Access Finance. Señora, tiene un credito vencido de $220.000. "
            "Debtor: No soy la titular, soy la hija. "
            "Agent: ¿Podria decirle que la llamamos de Access Finance para un asunto urgente? "
            "Debtor: Ella no esta. "
            "Agent: Por favor digale que nos llame al 800-123-456. Gracias, que tenga un buen dia."
        ),
    },
    {
        "Call_ID": "CALL-AF-003",
        "Empresa": "Access Finance",
        "Estatus": "Pagado",
        "Cuenta": "CTA-10102",
        "Grabacion": "https://storage.example.com/af-003.mp3",
        "Proveedor": "Colly",
        "createdTime": "2026-04-29T09:00:00",
        "Fecha de vencimiento": "2026-04-20",
        "Días de mora": 9,
        "Saldo vencido": 95000,
        "Saldo facturado": 95000,
        "Saldo total": 95000,
        "Transcrip": (
            "Agent: Buenos dias, habla Juan Perez de Access Finance, ¿hablo con el señor Ramirez? "
            "Debtor: Si, soy yo. "
            "Agent: Le llamo porque tiene un saldo pendiente de $95.000 con vencimiento el 20 de abril. "
            "Debtor: Si ya lo pague ayer por transferencia. "
            "Agent: Perfecto señor Ramirez, voy a verificar. ¿Tiene el comprobante? "
            "Debtor: Si, lo tengo. "
            "Agent: Le agradezco, queda registrado. Si hay algun problema le contactamos. "
            "Que tenga un excelente dia. "
            "Debtor: Igualmente, gracias."
        ),
    },

    # ── SISTECREDITO — mora media (31-90 dias) ───────────────────────────────
    {
        "Call_ID": "CALL-SC-001",
        "Empresa": "Sistecredito",
        "Estatus": "Promesa de pago",
        "Cuenta": "SC-55201",
        "Grabacion": "https://storage.example.com/sc-001.mp3",
        "Proveedor": "Colly",
        "createdTime": "2026-04-29T14:00:00",
        "Fecha de vencimiento": "2026-03-15",
        "Días de mora": 45,
        "Saldo vencido": 450000,
        "Saldo facturado": 500000,
        "Saldo total": 500000,
        "Transcrip": (
            "Agent: Buenas tardes, soy Ana Gutierrez de Sistecredito. "
            "¿Me comunico con la señora Fernandez? "
            "Debtor: Si, con ella habla. "
            "Agent: Señora Fernandez, le llamo porque tiene una deuda de $450.000 que lleva 45 dias vencida. "
            "Esto podria afectar su historial crediticio. "
            "Debtor: Estoy esperando que me paguen un trabajo, la semana que viene tengo para pagar. "
            "Agent: Entiendo. ¿Podria comprometerse a pagar el lunes 6 de mayo? "
            "Debtor: Si, el lunes pago. "
            "Agent: Muy bien, queda registrado su compromiso para el lunes 6 de mayo. "
            "Le recordamos que pagar a tiempo protege su credito. Hasta luego. "
            "Debtor: Hasta luego, gracias."
        ),
    },
    {
        "Call_ID": "CALL-SC-002",
        "Empresa": "Sistecredito",
        "Estatus": "Rechazado",
        "Cuenta": "SC-55389",
        "Grabacion": "https://storage.example.com/sc-002.mp3",
        "Proveedor": "Colly",
        "createdTime": "2026-04-29T15:30:00",
        "Fecha de vencimiento": "2026-03-01",
        "Días de mora": 59,
        "Saldo vencido": 780000,
        "Saldo facturado": 900000,
        "Saldo total": 900000,
        "Transcrip": (
            "Agent: Buenas tardes, habla con cobranzas de Sistecredito. ¿El señor Torres? "
            "Debtor: Si. ¿Que quiere? "
            "Agent: Señor Torres, tiene una deuda de $780.000 vencida. "
            "Debtor: No voy a pagar nada, esa deuda no es mia. "
            "Agent: Señor, segun nuestros registros usted firmo el contrato. "
            "Debtor: Eso es mentira, no me llamen mas. "
            "Agent: Entiendo que no esta de acuerdo. Puede presentar un reclamo formal en nuestras oficinas. "
            "Debtor: No me interesa. "
            "Agent: Queda registrado señor Torres. Que tenga buen dia."
        ),
    },
    {
        "Call_ID": "CALL-SC-003",
        "Empresa": "Sistecredito",
        "Estatus": "Comprometido",
        "Cuenta": "SC-55420",
        "Grabacion": "https://storage.example.com/sc-003.mp3",
        "Proveedor": "Colly",
        "createdTime": "2026-04-30T10:00:00",
        "Fecha de vencimiento": "2026-03-20",
        "Días de mora": 41,
        "Saldo vencido": 320000,
        "Saldo facturado": 320000,
        "Saldo total": 320000,
        "Transcrip": (
            "Agent: Buenos dias, le habla Pedro Salas de Sistecredito. Necesito hablar con el titular. "
            "Debtor: Si soy yo. "
            "Agent: Le llamo por su credito vencido de $320.000. ¿Como podemos ayudarle a regularizar su situacion? "
            "Debtor: Puedo pagar en cuotas, no todo junto. "
            "Agent: Podemos ver un plan de pago. ¿Cuanto podria pagar ahora? "
            "Debtor: Unos $100.000 ahora y el resto en dos cuotas. "
            "Agent: Perfecto, queda registrado compromiso de $100.000 esta semana y dos cuotas de $110.000. "
            "Le enviamos el detalle por correo. Hasta luego. "
            "Debtor: Gracias, hasta luego."
        ),
    },

    # ── RAPICREDIT — mora alta (>90 dias) ───────────────────────────────────
    {
        "Call_ID": "CALL-RC-001",
        "Empresa": "Rapicredit",
        "Estatus": "Negociacion",
        "Cuenta": "RC-88001",
        "Grabacion": "https://storage.example.com/rc-001.mp3",
        "Proveedor": "Colly",
        "createdTime": "2026-04-30T11:00:00",
        "Fecha de vencimiento": "2026-01-10",
        "Días de mora": 110,
        "Saldo vencido": 1200000,
        "Saldo facturado": 1400000,
        "Saldo total": 1400000,
        "Transcrip": (
            "Agent: Buenos dias, habla Sofia Reyes de Rapicredit. ¿El señor Vargas? "
            "Debtor: Si. "
            "Agent: Señor Vargas, tiene una deuda de $1.200.000 con 110 dias de mora. "
            "Es importante que regularice su situacion lo antes posible. "
            "Debtor: Estoy desempleado, no tengo como pagar. "
            "Agent: Entiendo su situacion. Tenemos opciones de refinanciamiento. "
            "¿Tiene algun ingreso aunque sea parcial? "
            "Debtor: Mi esposa trabaja, pero poco. "
            "Agent: Podriamos ofrecerle un plan especial de $50.000 mensuales por 24 meses. "
            "Debtor: Eso suena posible, pero necesito hablarlo con mi esposa. "
            "Agent: Por supuesto. ¿Podria confirmarme manana? "
            "Debtor: Si, llamenme manana. "
            "Agent: Perfecto, le llamamos manana. Que tenga buen dia señor Vargas."
        ),
    },
    {
        "Call_ID": "CALL-RC-002",
        "Empresa": "Rapicredit",
        "Estatus": "Incorrecto",
        "Cuenta": "RC-88045",
        "Grabacion": "https://storage.example.com/rc-002.mp3",
        "Proveedor": "Colly",
        "createdTime": "2026-04-30T14:00:00",
        "Fecha de vencimiento": "2026-01-25",
        "Días de mora": 95,
        "Saldo vencido": 850000,
        "Saldo facturado": 1000000,
        "Saldo total": 1000000,
        "Transcrip": (
            "Agent: ¿Hablo con el titular de la cuenta RC-88045? "
            "Debtor: Si. "
            "Agent: Tiene una deuda de $850.000, pague antes del viernes o mandamos a un cobrador. "
            "Debtor: No puede amenazarme asi. "
            "Agent: No es amenaza, es informacion. "
            "Debtor: Estoy grabando esta llamada. "
            "Agent: Esta bien. ¿Va a pagar o no? "
            "Debtor: Voy a poner una queja. Adios. "
            "Agent: Como quiera."
        ),
    },
    {
        "Call_ID": "CALL-RC-003",
        "Empresa": "Rapicredit",
        "Estatus": "Comprometido",
        "Cuenta": "RC-88067",
        "Grabacion": "https://storage.example.com/rc-003.mp3",
        "Proveedor": "Colly",
        "createdTime": "2026-05-01T09:30:00",
        "Fecha de vencimiento": "2026-01-30",
        "Días de mora": 91,
        "Saldo vencido": 620000,
        "Saldo facturado": 750000,
        "Saldo total": 750000,
        "Transcrip": (
            "Agent: Buenos dias, le habla Roberto Diaz de Rapicredit. ¿Hablo con la señora Castro? "
            "Debtor: Si, con ella. "
            "Agent: Señora Castro, le llamo por su credito con 91 dias de mora por $620.000. "
            "Queremos encontrar una solucion juntos. "
            "Debtor: Tuve un accidente y estuve hospitalizada, por eso no pude pagar. "
            "Agent: Lamento mucho lo que vivio señora Castro. Entendiendo su situacion, "
            "podemos ofrecerle una condonacion parcial de intereses si paga el capital. "
            "Debtor: ¿De cuanto seria el descuento? "
            "Agent: Podriamos condonar hasta un 30% de los intereses acumulados. "
            "Debtor: Eso me ayudaria mucho. Cuando salga del hospital la proxima semana puedo ir. "
            "Agent: Perfecto, queda registrado. Le deseamos una pronta recuperacion señora Castro. "
            "Debtor: Muchas gracias, hasta luego."
        ),
    },
]


def main():
    print(f"Cargando {len(LLAMADAS)} llamadas de ejemplo...")
    print(f"Backend: {BASE_URL}\n")

    exitosas = 0
    fallidas  = 0

    for i, llamada in enumerate(LLAMADAS, 1):
        try:
            r = requests.post(
                f"{BASE_URL}/api/v1/llamadas/ingesta",
                json=llamada,
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                print(f"  OK  [{i}] {llamada['Call_ID']} — {llamada['Empresa']} (id interno: {data['id_interno']})")
                exitosas += 1
            else:
                print(f"  ERR [{i}] {llamada['Call_ID']} — HTTP {r.status_code}: {r.text[:100]}")
                fallidas += 1
        except Exception as e:
            print(f"  ERR [{i}] {llamada['Call_ID']} — {e}")
            fallidas += 1

    print(f"\nResultado: {exitosas} cargadas | {fallidas} fallidas")
    print("\nAhora ve a http://localhost:8000/api/v1/auditoria/ejecutar (POST) para auditar todas con IA.")
    print("O espera hasta el ciclo automatico de 240 minutos.")


if __name__ == "__main__":
    main()
