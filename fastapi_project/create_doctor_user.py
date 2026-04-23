from sqlmodel import Session, select, create_engine
from models import User, Doctor, Sucursal
from passlib.context import CryptContext

# Setup compatible with main.py
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def create_doc_user():
    with Session(engine) as session:
        # 1. Get a Doctor (or create one)
        doctor = session.exec(select(Doctor)).first()
        if not doctor:
            print("No doctors found. Creating one...")
            # Need a Sucursal first
            sucursal = session.exec(select(Sucursal)).first()
            if not sucursal:
                 sucursal = Sucursal(nombre="Matriz", direccion="Av. Principal")
                 session.add(sucursal)
                 session.commit()
                 session.refresh(sucursal)
            
            doctor = Doctor(nombres="Juan", apellidos="Perez", cedula="1111", sucursal_id=sucursal.id)
            session.add(doctor)
            session.commit()
            session.refresh(doctor)
            print(f"Created Doctor: {doctor.nombres} {doctor.apellidos}")

        # 2. Check if user exists
        username = "doc1"
        user = session.exec(select(User).where(User.username == username)).first()
        if user:
            print(f"User {username} already exists.")
            # Update fields if needed
            if not user.doctor_id:
                user.doctor_id = doctor.id
                user.sucursal_id = doctor.sucursal_id
                user.role = "doctor"
                session.add(user)
                session.commit()
                print(f"Updated user {username} with doctor_id={doctor.id}")
        else:
            # Create User
            new_user = User(
                username=username,
                hashed_password=pwd_context.hash("doc1"),
                role="doctor",
                doctor_id=doctor.id,
                sucursal_id=doctor.sucursal_id
            )
            session.add(new_user)
            session.commit()
            print(f"Created user {username} linked to Doctor ID {doctor.id}")

if __name__ == "__main__":
    create_doc_user()
