import os

# Tests must never touch the real database or depend on the local .env.
# Environment variables take precedence over .env in pydantic-settings.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret-key-only-for-pytest-0123456789"

from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, hash_password
from app.database.database import Base, get_db
from app.main import app
from app.models.role import Role
from app.models.user import User


TEST_PASSWORD = "secret123"


@pytest.fixture(autouse=True)
def no_retry_sleep(monkeypatch):
    # Gemini retries back off with time.sleep; tests must not wait.
    monkeypatch.setattr("app.ai.gemini_http.time.sleep", lambda seconds: None)


@pytest.fixture
def db() -> Iterator[Session]:
    # SQLite accepts the pgvector VECTOR(768) column type name, so the
    # schema can be created; vector queries themselves are mocked.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    # SQLite ignores foreign keys unless asked; enable them so ON DELETE
    # CASCADE behaves as in PostgreSQL.
    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)

    session = sessionmaker(bind=engine, autoflush=False)()

    for role_name in ["admin", "user", "analyst"]:
        session.add(Role(name=role_name))

    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def create_user(db: Session) -> Callable[..., User]:

    def _create_user(
        username: str = "alice",
        role_name: str = "user",
        is_active: bool = True
    ) -> User:
        role = db.query(Role).filter(Role.name == role_name).one()

        user = User(
            username=username,
            email=f"{username}@example.com",
            full_name=username.title(),
            hashed_password=hash_password(TEST_PASSWORD),
            role_id=role.id,
            is_active=is_active
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    return _create_user


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token({"sub": str(user.id)})

    return {"Authorization": f"Bearer {token}"}
