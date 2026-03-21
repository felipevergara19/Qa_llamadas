from sqlmodel import create_engine, Session, SQLModel 

# 1. Las Coordenadas
POSTGRES_URL = "postgresql://postgres:Felipe19@localhost:5432/colektia_qa"

# 2. La Tubería Principal
engine = create_engine(POSTGRES_URL, echo=True)

# 3. El Constructor
def create_db_and_tables():
    """Conecta a la base de datos y crea las tablas que no existen."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Genera una sesión de base de datos para cada petición (endpoint)."""
    with Session(engine) as session:
        yield session