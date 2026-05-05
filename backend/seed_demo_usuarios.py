"""
seed_demo_usuarios.py -- Crea usuarios de demo para la presentacion.

Usuarios creados (todos con clave: Prueba123):
  - analista@colektia.com   | rol: analista_qa  | acceso global
  - cliente@access.com      | rol: cliente       | solo Access Finance
  - kam@rapicredit.com      | rol: kam           | solo Rapicredit

Uso:
  cd backend
  python seed_demo_usuarios.py
"""

from sqlmodel import Session, select
from database import engine
from models import Usuario, Cliente, RolUsuario
from auth import hash_password

CLAVE = "Prueba123"

USUARIOS_DEMO = [
    {
        "email":   "analista@colektia.com",
        "nombre":  "Ana Martinez (Analista QA)",
        "rol":     RolUsuario.analista_qa,
        "empresa": None,                    # acceso global, sin empresa
    },
    {
        "email":   "cliente@access.com",
        "nombre":  "Carlos Perez (Access Finance)",
        "rol":     RolUsuario.cliente,
        "empresa": "Access Finance",
    },
    {
        "email":   "kam@rapicredit.com",
        "nombre":  "Laura Gomez (Rapicredit KAM)",
        "rol":     RolUsuario.kam,
        "empresa": "Rapicredit",
    },
]


def get_or_create_empresa(session: Session, nombre: str) -> Cliente:
    empresa = session.exec(
        select(Cliente).where(Cliente.nombre_empresa == nombre)
    ).first()
    if not empresa:
        empresa = Cliente(nombre_empresa=nombre)
        session.add(empresa)
        session.commit()
        session.refresh(empresa)
        print(f"  [+] Empresa creada: {nombre}")
    else:
        print(f"  [=] Empresa ya existe: {nombre}")
    return empresa


def seed():
    print("\n=== Seed de usuarios demo ===\n")

    with Session(engine) as session:

        # -- Asegurar que las empresas existen ---------------------------------
        print("Verificando empresas...")
        empresas = {}
        for u in USUARIOS_DEMO:
            if u["empresa"] and u["empresa"] not in empresas:
                empresas[u["empresa"]] = get_or_create_empresa(session, u["empresa"])

        print("\nCreando usuarios...")

        for datos in USUARIOS_DEMO:
            existente = session.exec(
                select(Usuario).where(Usuario.email == datos["email"])
            ).first()

            if existente:
                print(f"  [=] Ya existe: {datos['email']}  (rol: {existente.rol})")
                continue

            cliente_id = None
            if datos["empresa"]:
                cliente_id = empresas[datos["empresa"]].id

            usuario = Usuario(
                email=datos["email"],
                nombre=datos["nombre"],
                password_hash=hash_password(CLAVE),
                rol=datos["rol"],
                cliente_id=cliente_id,
                activo=True,
            )
            session.add(usuario)
            session.commit()
            session.refresh(usuario)
            print(f"  [+] Creado: {datos['email']}  (rol: {usuario.rol})")

    print("\n=== Resumen de accesos ===")
    print(f"  admin@colektia.com       | Admin      | clave: {CLAVE}")
    print(f"  analista@colektia.com    | Analista QA| clave: {CLAVE}")
    print(f"  cliente@access.com       | Cliente    | clave: {CLAVE}")
    print(f"  kam@rapicredit.com       | KAM        | clave: {CLAVE}")
    print("\nListo. Puedes iniciar sesion con cualquiera de estos usuarios.\n")


if __name__ == "__main__":
    seed()
