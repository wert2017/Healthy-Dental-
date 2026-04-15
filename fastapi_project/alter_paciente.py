import sqlite3

def add_columns():
    db_path = "c:/HD/fastapi_project/database.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE paciente ADD COLUMN sexo VARCHAR")
        print("Column 'sexo' added.")
    except Exception as e:
        print(f"Skipping 'sexo': {e}")
        
    try:
        cursor.execute("ALTER TABLE paciente ADD COLUMN edad INTEGER")
        print("Column 'edad' added.")
    except Exception as e:
        print(f"Skipping 'edad': {e}")
        
    try:
        cursor.execute("ALTER TABLE paciente ADD COLUMN ciudad VARCHAR")
        print("Column 'ciudad' added.")
    except Exception as e:
        print(f"Skipping 'ciudad': {e}")
        
    conn.commit()
    conn.close()
    print("Database alteration complete.")

if __name__ == "__main__":
    add_columns()
