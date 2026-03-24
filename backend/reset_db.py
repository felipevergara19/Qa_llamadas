from sqlmodel import SQLModel
from database import engine
# Importamos los modelos para que el sistema sepa qué tablas crear
from models import Cliente, Llamada, Evaluacion 

def reiniciar_base_de_datos():
    print("Borrando tablas viejas...")
    SQLModel.metadata.drop_all(engine)
    
    print("Creando tablas nuevas con las columnas actualizadas...")
    SQLModel.metadata.create_all(engine)
    
    print("Base de datos reiniciada correctamente.")

if __name__ == "__main__":
    reiniciar_base_de_datos()