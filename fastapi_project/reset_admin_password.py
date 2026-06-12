from sqlmodel import Session, select
from database import engine
from models import User
from main import pwd_context

def reset():
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == "admin")).first()
        if user:
            user.hashed_password = pwd_context.hash("admin")
            session.add(user)
            session.commit()
            print("Password for user 'admin' reset to 'admin'.")
        else:
            print("User 'admin' not found.")

if __name__ == "__main__":
    reset()
