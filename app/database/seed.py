from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.models.role import Role
from app.models.user import User  # pyright: ignore[reportUnusedImport]

def seed_roles(db: Session):

    roles = [
        "admin",
        "user",
        "analyst"
    ]

    for role_name in roles:

        existing_role = db.query(Role).filter(
            Role.name == role_name
        ).first()

        if not existing_role:

            role = Role(
                name=role_name
            )

            db.add(role)

    db.commit()


def run_seed():

    db = SessionLocal()

    try:

        seed_roles(db)

    finally:

        db.close()


if __name__ == "__main__":

    run_seed()