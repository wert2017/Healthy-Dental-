from sqlalchemy import create_engine, text
import os

engine = create_engine(os.getenv('DATABASE_URL'))
p  = {'ini': '2026-05-01 00:00:00', 'fin': '2026-05-31 23:59:59'}
pj = {'ini': '2026-06-01 00:00:00', 'fin': '2026-06-30 23:59:59'}

print('=' * 55)
print('  VERIFICACION - DATOS DE MAYO 2026')
print('=' * 55)

with engine.connect() as c:
    at  = c.execute(text('SELECT COUNT(*) FROM atencion WHERE fecha BETWEEN :ini AND :fin'), p).scalar()
    ab  = c.execute(text('SELECT COUNT(*) FROM historialabono WHERE fecha BETWEEN :ini AND :fin'), p).scalar()
    gs  = c.execute(text('SELECT COUNT(*) FROM gasto WHERE fecha BETWEEN :ini AND :fin'), p).scalar()

    print(f'  atenciones mayo:       {at}')
    print(f'  historialabono mayo:   {ab}')
    print(f'  gastos mayo:           {gs}')
    print('=' * 55)

    if at == 0 and ab == 0 and gs == 0:
        print('  RESULTADO: TODO LIMPIO ✓')
    else:
        print('  RESULTADO: ATENCION - Aun quedan registros!')

    print()
    print('--- DATOS MASTER CONSERVADOS ---')
    pac = c.execute(text('SELECT COUNT(*) FROM paciente')).scalar()
    doc = c.execute(text('SELECT COUNT(*) FROM doctor')).scalar()
    suc = c.execute(text('SELECT COUNT(*) FROM sucursal')).scalar()
    tra = c.execute(text('SELECT COUNT(*) FROM tratamiento')).scalar()
    print(f'  pacientes:    {pac}')
    print(f'  doctores:     {doc}')
    print(f'  sucursales:   {suc}')
    print(f'  tratamientos: {tra}')

    print()
    print('--- DATOS JUNIO 2026 (produccion real) ---')
    atj = c.execute(text('SELECT COUNT(*) FROM atencion WHERE fecha BETWEEN :ini AND :fin'), pj).scalar()
    gsj = c.execute(text('SELECT COUNT(*) FROM gasto WHERE fecha BETWEEN :ini AND :fin'), pj).scalar()
    print(f'  atenciones junio: {atj}')
    print(f'  gastos junio:     {gsj}')
    print('=' * 55)
