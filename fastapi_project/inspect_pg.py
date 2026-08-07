import os

# Manual env parse
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

from sqlmodel import Session, select, text
from database import engine
from models import Paciente, Atencion, Pago, HistorialAbono, Sucursal, Doctor, AtencionDetalle

print("Connecting to DB URL:", engine.url)

with Session(engine) as session:
    pacientes = session.exec(select(Paciente).where(
        (Paciente.nombres.ilike('%ANIBAL%')) | 
        (Paciente.apellidos.ilike('%VERA%')) | 
        (Paciente.apellidos.ilike('%QUILLE%')) |
        (Paciente.historia_clinica.ilike('%1863%'))
    )).all()
    
    print(f"PACIENTES ENCONTRADOS ({len(pacientes)}):")
    for p in pacientes:
        print(f"ID: {p.id}, Nombre: {p.nombre_mostrar}, HC: {p.historia_clinica}, Saldo Favor (Abono): {p.saldo_favor}, Sucursal ID: {p.sucursal_id}")
        
        atenciones = session.exec(select(Atencion).where(Atencion.paciente_id == p.id)).all()
        for a in atenciones:
            print(f"\n  ATENCIÓN ID: {a.id}, Fecha: {a.fecha}, Estado: {a.estado}, Validado: {a.validado}, Doctor ID: {a.doctor_id}, Sucursal ID: {a.sucursal_id}, Obs: {a.observaciones}")
            pagos = session.exec(select(Pago).where(Pago.atencion_id == a.id)).all()
            for pg in pagos:
                print(f"    PAGO ID: {pg.id}, Forma: {pg.forma_pago}, Monto: {pg.monto}, Ref: {pg.referencia}, Fecha: {pg.fecha}")
            detalles = session.exec(select(AtencionDetalle).where(AtencionDetalle.atencion_id == a.id)).all()
            for d in detalles:
                print(f"    DETALLE ID: {d.id}, Tratamiento ID: {d.tratamiento_id}, Cant: {d.cantidad}, Unit: {d.precio_unitario}, Comision%: {d.porcentaje_comision}, Pagada: {d.comision_pagada}, MontoCom: {d.comision_pagada_monto}")
        
        abonos = session.exec(select(HistorialAbono).where(HistorialAbono.paciente_id == p.id)).all()
        print(f"  HISTORIAL ABONOS ({len(abonos)}):")
        for ab in abonos:
            print(f"    ABONO ID: {ab.id}, Monto: {ab.monto}, Metodo: {ab.metodo_pago}, Fecha: {ab.fecha}")

    print("\n--- ALL ATENCIONES ON 2026-07-27 ---")
    at27 = session.exec(select(Atencion).where(text("CAST(fecha AS TEXT) LIKE '2026-07-27%'"))).all()
    print(f"Atenciones on 2026-07-27: {len(at27)}")
    for a in at27:
        p = session.get(Paciente, a.paciente_id)
        pname = p.nombre_mostrar if p else "Desconocido"
        hc = p.historia_clinica if p else ""
        print(f"\n  ATENCIÓN ID: {a.id}, Paciente: {pname} ({hc}), Fecha: {a.fecha}, Estado: {a.estado}")
        pagos = session.exec(select(Pago).where(Pago.atencion_id == a.id)).all()
        for pg in pagos:
            print(f"    PAGO ID: {pg.id}, Forma: {pg.forma_pago}, Monto: {pg.monto}, Ref: {pg.referencia}, Fecha: {pg.fecha}")
        detalles = session.exec(select(AtencionDetalle).where(AtencionDetalle.atencion_id == a.id)).all()
        for d in detalles:
            print(f"    DETALLE ID: {d.id}, Doctor: {d.doctor_id}, Unit: {d.precio_unitario}, Comision%: {d.porcentaje_comision}, Pagada: {d.comision_pagada}")
