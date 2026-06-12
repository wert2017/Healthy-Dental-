import os
import sys

# Manually load .env from workspace
env_path = os.path.join("c:", os.sep, "Users", "HP 1000", "Desktop", "HD Web", ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

from sqlmodel import Session, create_engine, select
sys.path.append(os.path.join("c:", os.sep, "Users", "HP 1000", "Desktop", "HD Web", "fastapi_project"))
from models import HistorialAbono, Paciente, User, Sucursal

db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

with Session(engine) as session:
    abono = session.get(HistorialAbono, 64)
    if abono:
        patient = session.get(Paciente, abono.paciente_id)
        user_reg = session.get(User, abono.usuario_id)
        
        patient_suc = session.get(Sucursal, patient.sucursal_id) if patient and patient.sucursal_id else None
        user_suc = session.get(Sucursal, user_reg.sucursal_id) if user_reg and user_reg.sucursal_id else None
        
        print("--- DETALLE ABONO ID 64 ---")
        print(f"ID: {abono.id}")
        print(f"Fecha: {abono.fecha}")
        print(f"Monto: {abono.monto}")
        print(f"Metodo Pago: {abono.metodo_pago}")
        print(f"Paciente: {patient.nombres} {patient.apellidos} | Sucursal Paciente: {patient_suc.nombre if patient_suc else 'None'} (ID: {patient.sucursal_id})")
        print(f"Usuario Registrador: {user_reg.username} | Sucursal Usuario: {user_suc.nombre if user_suc else 'None'} (ID: {user_reg.sucursal_id})")
    else:
        print("Abono ID 64 no encontrado.")
