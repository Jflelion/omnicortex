from app.core.security import create_access_token
from app.models.user import User
from tests.conftest import TEST_PASSWORD, auth_headers


def login(client, username: str, password: str):
    return client.post(
        "/auth/login",
        data={"username": username, "password": password}
    )


def test_login_returns_token(client, create_user):
    create_user("alice")

    response = login(client, "alice", TEST_PASSWORD)

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"

    me = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {response.json()['access_token']}"}
    )

    assert me.status_code == 200
    assert me.json()["username"] == "alice"


def test_login_with_wrong_password(client, create_user):
    create_user("alice")

    assert login(client, "alice", "wrong").status_code == 401


def test_login_with_unknown_user(client):
    assert login(client, "ghost", TEST_PASSWORD).status_code == 401


def test_invalid_token_is_rejected(client):
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer not-a-jwt"}
    )

    assert response.status_code == 401


def test_missing_token_is_rejected(client):
    assert client.get("/auth/me").status_code == 401


def test_token_with_username_subject_is_rejected(client, create_user):
    create_user("alice")
    token = create_access_token({"sub": "alice"})

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401


def test_token_survives_username_change(client, db, create_user):
    user = create_user("alice")
    headers = auth_headers(user)

    user.username = "alice_renamed"
    db.commit()

    response = client.get("/auth/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["username"] == "alice_renamed"


def test_inactive_user_is_rejected(client, create_user):
    user = create_user("alice", is_active=False)

    response = client.get("/auth/me", headers=auth_headers(user))

    assert response.status_code == 400


def test_normal_user_cannot_access_admin_routes(client, create_user):
    user = create_user("alice", role_name="user")
    headers = auth_headers(user)

    assert client.get(f"/users/{user.id}", headers=headers).status_code == 403
    assert client.delete(f"/users/{user.id}", headers=headers).status_code == 403
    assert client.post("/roles/", json={"name": "hacker"}, headers=headers).status_code == 403


def test_admin_can_access_admin_routes(client, create_user):
    admin = create_user("root", role_name="admin")
    other = create_user("alice")

    response = client.get(f"/users/{other.id}", headers=auth_headers(admin))

    assert response.status_code == 200
    assert response.json()["username"] == "alice"


def test_public_registration_always_gets_user_role(client, db):
    response = client.post(
        "/users/",
        json={
            "username": "mallory",
            "email": "mallory@example.com",
            "password": "secret123",
            "role_id": 1
        }
    )

    assert response.status_code == 201
    assert response.json()["role"]["name"] == "user"
    assert db.query(User).filter(User.username == "mallory").one().role.name == "user"


def test_registration_rejects_duplicate_username(client, create_user):
    create_user("alice")

    response = client.post(
        "/users/",
        json={
            "username": "alice",
            "email": "other@example.com",
            "password": "secret123"
        }
    )

    assert response.status_code == 409
