from sqlmodel import Session
from database import engine
from models import Cliente

def inyectar_cliente():
    with Session(engine) as db:
        # Creamos al cliente Access Finance con las reglas de tu Excel
        cliente_prueba = Cliente(
            nombre_empresa="Access Finance",
            guion_identificacion="Te llamo de tarjeta de crédito Yazt ¿hablo con [nombre titular]?",
            guion_saludo="Hola, [nombre titular]",
            guion_entrega_mensaje="El motivo de mi llamada es porque tienes un saldo pendiente de [valor cuota]. ¿En qué fecha podrías realizar el pago?",
            guion_negociacion="¿Me puedes contar qué ha hecho que no hayas podido ponerte al día con el pago? Quiero entender mejor tu situación.",
            guion_agenda_compromiso="Perfecto. Para registrarlo correctamente: ¿confirmas que vas a realizar el pago el [fecha acordada]?",
            guion_cierre="Recuerda que mientras más tiempo dejes sin pagar, más intereses puedes acumular.",
            reglas_adicionales="Segmento: Preventiva. Tono humano, empático y profesional."
        )
        db.add(cliente_prueba)
        db.commit()
        print("✅ Cliente 'Access Finance' inyectado en la Base de Datos con su guion.")

if __name__ == "__main__":
    inyectar_cliente()