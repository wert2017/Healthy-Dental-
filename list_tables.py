import sqlite3
db_path = r'C:\Users\HP 1000\Desktop\HD Web\db.sqlite3'
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
print([r[0] for r in cur.fetchall()])
conn.close()
