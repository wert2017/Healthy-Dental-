import sqlite3

def inspect_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    print("--- SUCURSALES ---")
    cursor.execute("SELECT * FROM sucursal")
    for row in cursor.fetchall():
        print(row)
        
    print("\n--- USERS ---")
    try:
        cursor.execute("SELECT id, username, role, sucursal_id FROM user")
        for row in cursor.fetchall():
            print(row)
    except Exception as e:
        print(f"Error reading users: {e}")
        
    conn.close()

if __name__ == "__main__":
    inspect_db()
