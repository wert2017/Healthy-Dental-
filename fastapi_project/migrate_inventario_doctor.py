import sqlite3

def migrate():
    print("Starting Doctor Personal Inventory Migration...")
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Create INVENTARIODOCTOR table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventariodoctor (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id INTEGER NOT NULL REFERENCES doctor(id),
        insumo_id INTEGER NOT NULL REFERENCES insumo(id),
        stock_actual INTEGER NOT NULL DEFAULT 0
    );
    ''')
    print("- Table INVENTARIODOCTOR ensured.")
    
    conn.commit()
    conn.close()
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
