import sqlite3

conn = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("--- SEARCH ALL PATIENTS CONTAINING ANIBAL OR QUILLE OR 1863 ---")
cursor.execute("SELECT * FROM paciente WHERE nombres LIKE '%ANIBAL%' OR apellidos LIKE '%QUILLE%' OR historia_clinica LIKE '%1863%'")
pats = cursor.fetchall()
print("Found patients:", len(pats))
for p in pats:
    print(dict(p))

print("\n--- SEARCH ATENCIONES WHERE OBSERVACIONES OR FECHA OR DETAILS ---")
cursor.execute("SELECT * FROM atencion ORDER BY id DESC LIMIT 20")
for a in cursor.fetchall():
    print(dict(a))

print("\n--- SEARCH ALL PAGOS ---")
cursor.execute("SELECT * FROM pago ORDER BY id DESC LIMIT 30")
for pg in cursor.fetchall():
    print(dict(pg))

print("\n--- SEARCH ATENCIONDETALLE WITH PROTESIS ---")
cursor.execute("SELECT d.*, t.nombre FROM atenciondetalle d JOIN tratamiento t ON d.tratamiento_id = t.id WHERE t.nombre LIKE '%protesis%' OR t.nombre LIKE '%Protesis%' ORDER BY d.id DESC LIMIT 20")
for d in cursor.fetchall():
    print(dict(d))
