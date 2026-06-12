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
from models import Pago, HistorialAbono, Gasto, Atencion, User, Sucursal
from sqlalchemy import func

db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

print("Calculating cash breakdown...")

with Session(engine) as session:
    # 1. Check Sucursal base info
    sucursal = session.get(Sucursal, 1) # Assuming sucursal_id = 1
    print(f"Sucursal: {sucursal.nombre} | Fondo Caja (Referencia): {sucursal.fondo_caja}")

    # 2. Historical Cash Payments from Treatments
    pago_trat_cash = session.exec(
        select(func.sum(Pago.monto))
        .join(Atencion)
        .where(Atencion.sucursal_id == 1)
        .where(Pago.forma_pago == "EF")
    ).first() or 0.0
    print(f"Historical Cash Treatment Payments (Pago.forma_pago == 'EF'): ${pago_trat_cash:.2f}")

    # 3. Historical Cash Wallet Recharges
    recharges_cash = session.exec(
        select(func.sum(HistorialAbono.monto))
        .join(User, HistorialAbono.usuario_id == User.id)
        .where(User.sucursal_id == 1)
        .where(HistorialAbono.metodo_pago == "EFECTIVO")
    ).first() or 0.0
    print(f"Historical Cash Wallet Recharges (HistorialAbono.metodo_pago == 'EFECTIVO'): ${recharges_cash:.2f}")

    # 4. Historical Cash Expenses
    expenses_cash = session.exec(
        select(func.sum(Gasto.monto))
        .where(Gasto.sucursal_id == 1)
        .where(Gasto.metodo_pago == "EFECTIVO")
    ).first() or 0.0
    print(f"Historical Cash Expenses (Gasto.metodo_pago == 'EFECTIVO'): ${expenses_cash:.2f}")

    # Calculate net historical efectivo balance
    net_hist_efectivo = (pago_trat_cash + recharges_cash) - expenses_cash
    print(f"Net Historical Cash Balance: ${net_hist_efectivo:.2f}")

    # 5. Let's list all June 2026 Cash Incomes (Payments + Recharges)
    import datetime
    june_start = datetime.datetime(2026, 6, 1, 0, 0, 0)
    june_end = datetime.datetime(2026, 6, 30, 23, 59, 59)

    june_pago_trat = session.exec(
        select(func.sum(Pago.monto))
        .join(Atencion)
        .where(Atencion.sucursal_id == 1)
        .where(Pago.forma_pago == "EF")
        .where(Atencion.fecha >= june_start)
        .where(Atencion.fecha <= june_end)
    ).first() or 0.0
    print(f"\nJune 2026 Cash Treatment Payments: ${june_pago_trat:.2f}")

    june_recharges = session.exec(
        select(func.sum(HistorialAbono.monto))
        .join(User, HistorialAbono.usuario_id == User.id)
        .where(User.sucursal_id == 1)
        .where(HistorialAbono.metodo_pago == "EFECTIVO")
        .where(HistorialAbono.fecha >= june_start)
        .where(HistorialAbono.fecha <= june_end)
    ).first() or 0.0
    print(f"June 2026 Cash Wallet Recharges: ${june_recharges:.2f}")

    june_total_ingresos = june_pago_trat + june_recharges
    print(f"Total June 2026 Cash Incomes: ${june_total_ingresos:.2f}")

    # 6. June 2026 Cash Expenses
    june_expenses = session.exec(
        select(func.sum(Gasto.monto))
        .where(Gasto.sucursal_id == 1)
        .where(Gasto.metodo_pago == "EFECTIVO")
        .where(Gasto.fecha >= june_start)
        .where(Gasto.fecha <= june_end)
    ).first() or 0.0
    print(f"June 2026 Cash Expenses: ${june_expenses:.2f}")

    # 7. Let's see if there are any cash movements BEFORE June 2026
    prev_pago_trat = session.exec(
        select(func.sum(Pago.monto))
        .join(Atencion)
        .where(Atencion.sucursal_id == 1)
        .where(Pago.forma_pago == "EF")
        .where(Atencion.fecha < june_start)
    ).first() or 0.0
    prev_recharges = session.exec(
        select(func.sum(HistorialAbono.monto))
        .join(User, HistorialAbono.usuario_id == User.id)
        .where(User.sucursal_id == 1)
        .where(HistorialAbono.metodo_pago == "EFECTIVO")
        .where(HistorialAbono.fecha < june_start)
    ).first() or 0.0
    prev_expenses = session.exec(
        select(func.sum(Gasto.monto))
        .where(Gasto.sucursal_id == 1)
        .where(Gasto.metodo_pago == "EFECTIVO")
        .where(Gasto.fecha < june_start)
    ).first() or 0.0

    print(f"\nPre-June Cash Payments: ${prev_pago_trat:.2f}")
    print(f"Pre-June Cash Recharges: ${prev_recharges:.2f}")
    print(f"Pre-June Cash Expenses: ${prev_expenses:.2f}")
    print(f"Pre-June Net Cash Balance: ${(prev_pago_trat + prev_recharges - prev_expenses):.2f}")

    # Let's list details of all Cash Incomes in June
    print("\n--- DETAIL OF CASH TREATMENT PAYMENTS IN JUNE ---")
    query_pago_det = select(Pago, Atencion).join(Atencion).where(Atencion.sucursal_id == 1).where(Pago.forma_pago == "EF").where(Atencion.fecha >= june_start).where(Atencion.fecha <= june_end)
    res_p = session.exec(query_pago_det).all()
    for p, a in res_p:
        print(f"AtencionID: {a.id} | Fecha: {a.fecha} | Monto: {p.monto}")

    print("\n--- DETAIL OF CASH WALLET RECHARGES IN JUNE ---")
    query_rec_det = select(HistorialAbono).join(User, HistorialAbono.usuario_id == User.id).where(User.sucursal_id == 1).where(HistorialAbono.metodo_pago == "EFECTIVO").where(HistorialAbono.fecha >= june_start).where(HistorialAbono.fecha <= june_end)
    res_r = session.exec(query_rec_det).all()
    for h in res_r:
        print(f"AbonoID: {h.id} | Fecha: {h.fecha} | Monto: {h.monto}")

    print("\n--- DETAIL OF CASH EXPENSES IN JUNE ---")
    query_g_det = select(Gasto).where(Gasto.sucursal_id == 1).where(Gasto.metodo_pago == "EFECTIVO").where(Gasto.fecha >= june_start).where(Gasto.fecha <= june_end)
    res_g = session.exec(query_g_det).all()
    for g in res_g:
        print(f"GastoID: {g.id} | Fecha: {g.fecha} | Desc: {g.descripcion} | Monto: {g.monto} | Cat: {g.categoria}")
