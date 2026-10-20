import os
from sqlmodel import SQLModel, create_engine, Session

# Priority: Environment variable (Railway/Production)
# Fallback: Local SQLite
sqlite_file_name = "database.db"
database_url = os.getenv("DATABASE_URL", f"sqlite:///{sqlite_file_name}")

# Fix for PostgreSQL URL provided by Railway (starts with postgres:// but SQLAlchemy needs postgresql://)
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

connect_args = {}
if database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(database_url, echo=False, connect_args=connect_args)

def create_db_and_tables():
    try:
        SQLModel.metadata.create_all(engine)
    except Exception as e:
        print(f"Skipping create_all due to error: {e}")

    # Migrations: add columns that may not exist in older DB versions
    migrations = [
        "ALTER TABLE sucursal ADD COLUMN IF NOT EXISTS fondo_caja NUMERIC(10,2) DEFAULT 0",
        "ALTER TABLE sucursal ADD COLUMN IF NOT EXISTS fondo_banco NUMERIC(10,2) DEFAULT 0",
        "ALTER TABLE sucursal ADD COLUMN IF NOT EXISTS telefono VARCHAR(50) DEFAULT NULL",
        "ALTER TABLE doctor ADD COLUMN IF NOT EXISTS google_calendar_id VARCHAR(255) DEFAULT NULL",
        "ALTER TABLE historialabono ADD COLUMN IF NOT EXISTS concepto VARCHAR(255) DEFAULT 'Abono General'",
        "ALTER TABLE certificadomedico ADD COLUMN IF NOT EXISTS sucursal_emision_nombre VARCHAR(255) DEFAULT ''",
        "ALTER TABLE certificadomedico ADD COLUMN IF NOT EXISTS sucursal_emision_direccion VARCHAR(255) DEFAULT ''",
        "ALTER TABLE certificadomedico ADD COLUMN IF NOT EXISTS sucursal_emision_telefono VARCHAR(50) DEFAULT ''",
        # Nuevas columnas módulo Compras/Inventario (v2)
        "ALTER TABLE proveedor ADD COLUMN IF NOT EXISTS ruc VARCHAR(50) DEFAULT NULL",
        "ALTER TABLE proveedor ADD COLUMN IF NOT EXISTS direccion VARCHAR(255) DEFAULT NULL",
        "ALTER TABLE compra ADD COLUMN IF NOT EXISTS bodega_id INTEGER DEFAULT 1",
        "ALTER TABLE compra ADD COLUMN IF NOT EXISTS numero_autorizacion VARCHAR(100) DEFAULT NULL",
        "ALTER TABLE compra ADD COLUMN IF NOT EXISTS subtotal_15 NUMERIC(10,2) DEFAULT 0",
        "ALTER TABLE compra ADD COLUMN IF NOT EXISTS subtotal_0 NUMERIC(10,2) DEFAULT 0",
        "ALTER TABLE compra ADD COLUMN IF NOT EXISTS subtotal_sin_impuestos NUMERIC(10,2) DEFAULT 0",
        "ALTER TABLE compra ADD COLUMN IF NOT EXISTS iva_porcentaje NUMERIC(5,2) DEFAULT 15",
        "ALTER TABLE compra ADD COLUMN IF NOT EXISTS monto_iva NUMERIC(10,2) DEFAULT 0",
        "ALTER TABLE compra ADD COLUMN IF NOT EXISTS descuento NUMERIC(10,2) DEFAULT 0",
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(__import__("sqlalchemy").text(sql))
            except Exception:
                # Handle SQLite where IF NOT EXISTS might not be supported
                try:
                    clean_sql = sql.replace("IF NOT EXISTS ", "")
                    conn.execute(__import__("sqlalchemy").text(clean_sql))
                except Exception:
                    pass
        conn.commit()

def get_session():
    with Session(engine) as session:
        yield session
