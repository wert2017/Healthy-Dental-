import sqlite3

# Buscar en AMBAS bases de datos
for db_path in [
    r'C:\HD\db.sqlite3',
    r'C:\HD\db_backup_paso2.sqlite3',
    r'C:\Users\HP 1000\Desktop\HD Web\fastapi_project\database.db',
]:
    print(f"\n{'='*60}")
    print(f"BD: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tablas = [r[0] for r in cur.fetchall()]
        print(f"Tablas: {tablas}")

        # Buscar en tabla paciente o pacientes_paciente
        for tabla in ['paciente', 'pacientes_paciente']:
            if tabla in tablas:
                cur.execute(f"SELECT * FROM {tabla} WHERE nombres LIKE ? OR historia_clinica LIKE ?",
                            ('%NIXON%', '%0315%'))
                rows = cur.fetchall()
                if rows:
                    print(f"\n[{tabla}] NIXON encontrado:")
                    for r in rows:
                        print(dict(r))

                    # Buscar atenciones
                    paciente_id = rows[0]['id']
                    for tabla_at in ['atencion', 'atenciones_atencion']:
                        if tabla_at in tablas:
                            cur.execute(f"SELECT * FROM {tabla_at} WHERE paciente_id = ?", (paciente_id,))
                            ats = cur.fetchall()
                            print(f"\nAtenciones en [{tabla_at}]:")
                            for a in ats:
                                print(dict(a))
                else:
                    print(f"[{tabla}] No se encontró NIXON")

        conn.close()
    except Exception as e:
        print(f"Error: {e}")
