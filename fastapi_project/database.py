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

def get_session():
    with Session(engine) as session:
        yield session
