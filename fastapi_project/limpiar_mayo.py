"""
Script: limpiar_mayo.py
Propósito: Eliminar todos los datos transaccionales de Mayo 2026 de producción.
Conserva: pacientes, doctores, sucursales, usuarios, tratamientos, inventario.

Ejecutar desde Railway Console (web service):
    python fastapi_project/limpiar_mayo.py
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text

# ── Conexión a la base de datos ─────────────────────────────────────────────
database_url = os.getenv("DATABASE_URL", "")
if not database_url:
    print("❌ ERROR: No se encontró la variable DATABASE_URL.")
    print("   Asegúrate de ejecutar esto desde la consola de Railway.")
    sys.exit(1)

if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(database_url)

# ── Rango de fechas: todo Mayo 2026 ────────────────────────────────────────
FECHA_INICIO = "2026-05-01 00:00:00"
FECHA_FIN    = "2026-05-31 23:59:59"

print("=" * 60)
print("  LIMPIEZA DE DATOS - MAYO 2026")
print("=" * 60)
print(f"  Rango: {FECHA_INICIO}  →  {FECHA_FIN}")
print("=" * 60)

with engine.connect() as conn:

    # ── 1. PREVIEW: cuántos registros se van a borrar ──────────────────────
    print("\n📊 CONTEO DE REGISTROS A ELIMINAR:\n")

    conteos = {
        "atencion":         "SELECT COUNT(*) FROM atencion WHERE fecha BETWEEN :ini AND :fin",
        "historialabono":   "SELECT COUNT(*) FROM historialabono WHERE fecha BETWEEN :ini AND :fin",
        "gasto":            "SELECT COUNT(*) FROM gasto WHERE fecha BETWEEN :ini AND :fin",
    }

    params = {"ini": FECHA_INICIO, "fin": FECHA_FIN}
    totales = {}

    for tabla, query in conteos.items():
        try:
            result = conn.execute(text(query), params)
            count = result.scalar()
            totales[tabla] = count
            print(f"   {tabla:<25} → {count} registros")
        except Exception as e:
            print(f"   {tabla:<25} → ERROR: {e}")
            totales[tabla] = 0

    # Detalles y pagos (en cascada con atencion)
    try:
        r = conn.execute(text(
            "SELECT COUNT(*) FROM atenciondetalle ad "
            "JOIN atencion a ON ad.atencion_id = a.id "
            "WHERE a.fecha BETWEEN :ini AND :fin"
        ), params)
        count_det = r.scalar()
        print(f"   {'atenciondetalle (cascada)':<25} → {count_det} registros")
    except Exception as e:
        print(f"   atenciondetalle (cascada)   → ERROR: {e}")
        count_det = 0

    try:
        r = conn.execute(text(
            "SELECT COUNT(*) FROM pago p "
            "JOIN atencion a ON p.atencion_id = a.id "
            "WHERE a.fecha BETWEEN :ini AND :fin"
        ), params)
        count_pag = r.scalar()
        print(f"   {'pago (cascada)':<25} → {count_pag} registros")
    except Exception as e:
        print(f"   pago (cascada)              → ERROR: {e}")
        count_pag = 0

    try:
        r = conn.execute(text(
            "SELECT COUNT(*) FROM auditoriaatencion au "
            "JOIN atencion a ON au.atencion_id = a.id "
            "WHERE a.fecha BETWEEN :ini AND :fin"
        ), params)
        count_aud = r.scalar()
        print(f"   {'auditoriaatencion (cascada)':<25} → {count_aud} registros")
    except Exception as e:
        print(f"   auditoriaatencion (cascada) → ERROR: {e}")
        count_aud = 0

    total_general = sum(totales.values()) + count_det + count_pag + count_aud
    print(f"\n   {'TOTAL':<25} → {total_general} registros")

    if total_general == 0:
        print("\n✅ No hay datos de Mayo 2026 para eliminar. Nada que hacer.")
        sys.exit(0)

    # ── 2. CONFIRMACIÓN ────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  ⚠️  ESTA ACCIÓN ES IRREVERSIBLE")
    print("=" * 60)
    confirmacion = input("\n¿Confirmas que deseas eliminar estos datos? (escribe 'SI' para continuar): ")

    if confirmacion.strip().upper() != "SI":
        print("\n❌ Operación cancelada. No se eliminó nada.")
        sys.exit(0)

    # ── 3. ELIMINACIÓN en orden correcto ───────────────────────────────────
    print("\n🗑️  Iniciando eliminación...\n")

    try:
        # 3a. HistorialAbono de mayo (tabla independiente)
        r = conn.execute(text(
            "DELETE FROM historialabono WHERE fecha BETWEEN :ini AND :fin"
        ), params)
        print(f"   ✅ historialabono eliminados:     {r.rowcount}")

        # 3b. Atenciones de mayo (CASCADE elimina: atenciondetalle, pago, auditoriaatencion)
        r = conn.execute(text(
            "DELETE FROM atencion WHERE fecha BETWEEN :ini AND :fin"
        ), params)
        print(f"   ✅ atenciones eliminadas:         {r.rowcount}")
        print(f"      (detalles, pagos y auditoría eliminados en cascada)")

        # 3c. Gastos de mayo
        r = conn.execute(text(
            "DELETE FROM gasto WHERE fecha BETWEEN :ini AND :fin"
        ), params)
        print(f"   ✅ gastos eliminados:             {r.rowcount}")

        conn.commit()

        print("\n" + "=" * 60)
        print("  ✅ LIMPIEZA COMPLETADA EXITOSAMENTE")
        print(f"  Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERROR durante la eliminación: {e}")
        print("   Se hizo ROLLBACK. No se eliminó nada.")
        sys.exit(1)
