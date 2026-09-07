import os
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

from database import engine
from sqlmodel import Session, select, delete
from models import Sucursal, DoctorSucursal

print("Connecting to DB:", engine.url)
with Session(engine) as session:
    invalid_names = ["HEALTHY DENTAL LA MAGDALENA", "Sucursal Norte"]
    deleted_count = 0
    for name in invalid_names:
        sucursales = session.exec(select(Sucursal).where(Sucursal.nombre == name)).all()
        for s in sucursales:
            print(f"Eliminando sucursal inválida #{s.id}: '{s.nombre}'")
            # Remove links in DoctorSucursal if any
            links = session.exec(select(DoctorSucursal).where(DoctorSucursal.sucursal_id == s.id)).all()
            for link in links:
                session.delete(link)
            session.delete(s)
            deleted_count += 1
            
    session.commit()
    print(f"Limpieza completada! {deleted_count} sucursales inválidas eliminadas.")

    remaining = session.exec(select(Sucursal)).all()
    print("SUCURSALES VÁLIDAS RESTANTES:")
    for s in remaining:
        print(f"  ID #{s.id}: '{s.nombre}'")
