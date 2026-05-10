from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy import text

# 1. Las Coordenadas
POSTGRES_URL = "postgresql://postgres:Felipe19@localhost:5432/colektia_qa"

# 2. La Tubería Principal
engine = create_engine(POSTGRES_URL, echo=True)

# 3. El Constructor
def create_db_and_tables():
    """Conecta a la base de datos y crea las tablas que no existen."""
    SQLModel.metadata.create_all(engine)
    _run_migrations()

def _run_migrations():
    """Aplica columnas nuevas sin romper datos existentes (ALTER TABLE IF NOT EXISTS)."""
    migraciones = [
        # HU12: Versionado de rúbricas
        "ALTER TABLE rubrica    ADD COLUMN IF NOT EXISTS version     INTEGER DEFAULT 1",
        "ALTER TABLE evaluacion ADD COLUMN IF NOT EXISTS rubrica_id  INTEGER REFERENCES rubrica(id)",
    ]
    with engine.connect() as conn:
        for sql in migraciones:
            conn.execute(text(sql))
        conn.commit()

def get_session():
    """Genera una sesión de base de datos para cada petición (endpoint)."""
    with Session(engine) as session:
        yield session