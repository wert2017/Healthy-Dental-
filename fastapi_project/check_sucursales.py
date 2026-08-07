import os

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

from sqlmodel import Session, select
from database import engine
from models import Sucursal, Pago, Atencion, Paciente

with Session(engine) as session:
    sucursales = session.exec(select(Sucursal)).all()
    for s in sucursales:
        print(f"Sucursal ID: {s.id}, Nombre: {s.nombre}, Fondo Caja: {s.fondo_caja}, Fondo Banco: {s.fondo_banco}")
