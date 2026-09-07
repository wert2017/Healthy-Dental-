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
from sqlmodel import Session, select
from models import Sucursal, Paciente, Doctor, DoctorSucursal, Atencion, User, Gasto

print("Connecting to DB:", engine.url)
with Session(engine) as session:
    all_sucursales = session.exec(select(Sucursal)).all()
    print("TODAS LAS SUCURSALES EN DB:")
    for s in all_sucursales:
        p_cnt = len(session.exec(select(Paciente).where(Paciente.sucursal_id == s.id)).all())
        d_cnt = len(session.exec(select(Doctor).where(Doctor.sucursal_id == s.id)).all())
        a_cnt = len(session.exec(select(Atencion).where(Atencion.sucursal_id == s.id)).all())
        u_cnt = len(session.exec(select(User).where(User.sucursal_id == s.id)).all())
        g_cnt = len(session.exec(select(Gasto).where(Gasto.sucursal_id == s.id)).all())
        print(f"  ID #{s.id}: '{s.nombre}' -> Pacientes={p_cnt}, Doctores={d_cnt}, Atenciones={a_cnt}, Users={u_cnt}, Gastos={g_cnt}")
