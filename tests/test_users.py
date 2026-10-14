from unittest.mock import MagicMock

import pytest

from app.models.role import Role
from app.services import embedding_service
from tests.conftest import auth_headers


def register(client, **overrides):
    payload = {
        "username": "bob",
        "email": "bob@example.com",
        "password": "secret123",
    }
    payload.update(overrides)

    return client.post("/users/", json=payload)


@pytest.mark.parametrize(
    "overrides",
    [
        {"password": "short"},
        {"username": "ab"},
        {"username": "con espacios"},
        {"username": "   "},
        {"email": "not-an-email"},
    ]
)
def test_registration_validates_input(client, overrides):
    assert register(client, **overrides).status_code == 422


def test_registration_accepts_valid_input(client):
    assert register(client).status_code == 201


def test_admin_cannot_lock_themselves_out(client, db, create_user):
    admin = create_user("root", role_name="admin")
    headers = auth_headers(admin)
    user_role = db.query(Role).filter(Role.name == "user").one()

    assert client.patch(f"/users/{admin.id}/deactivate", headers=headers).status_code == 400
    assert client.delete(f"/users/{admin.id}", headers=headers).status_code == 400
    assert client.put(
        f"/users/{admin.id}", json={"role_id": user_role.id}, headers=headers
    ).status_code == 400
    assert client.put(
        f"/users/{admin.id}", json={"is_active": False}, headers=headers
    ).status_code == 400

    db.refresh(admin)
    assert admin.is_active
    assert admin.role.name == "admin"


def test_admin_can_still_edit_own_profile(client, create_user):
    admin = create_user("root", role_name="admin")

    response = client.put(
        f"/users/{admin.id}", json={"full_name": "Root Admin"}, headers=auth_headers(admin)
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Root Admin"


def test_admin_can_manage_other_users(client, create_user):
    admin = create_user("root", role_name="admin")
    other = create_user("alice")
    headers = auth_headers(admin)

    assert client.patch(f"/users/{other.id}/deactivate", headers=headers).status_code == 200
    assert client.delete(f"/users/{other.id}", headers=headers).status_code == 204


def test_update_rejects_null_role_and_duplicate_email(client, create_user):
    admin = create_user("root", role_name="admin")
    other = create_user("alice")
    headers = auth_headers(admin)

    assert client.put(
        f"/users/{other.id}", json={"role_id": None}, headers=headers
    ).status_code == 422
    assert client.put(
        f"/users/{other.id}", json={"email": "root@example.com"}, headers=headers
    ).status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        {"query": ""},
        {"query": "   "},
        {"query": "hola", "limit": 0},
        {"query": "hola", "limit": 1000},
    ]
)
def test_search_validates_input(client, create_user, payload):
    user = create_user("alice")

    response = client.post("/documents/search", json=payload, headers=auth_headers(user))

    assert response.status_code == 422


@pytest.mark.parametrize("question", ["", "   "])
def test_ask_rejects_blank_questions(client, create_user, question):
    user = create_user("alice")

    response = client.post(
        "/documents/ask", json={"question": question}, headers=auth_headers(user)
    )

    assert response.status_code == 422


def test_ollama_embedding_uses_api_embed(monkeypatch):
    monkeypatch.setattr(embedding_service.settings, "EMBEDDING_PROVIDER", "ollama")
    response = MagicMock()
    response.json.return_value = {"embeddings": [[0.5, 0.25]]}
    post = MagicMock(return_value=response)
    monkeypatch.setattr(embedding_service.requests, "post", post)

    assert embedding_service.generate_embedding("hola") == [0.5, 0.25]

    assert post.call_args.args[0].endswith("/api/embed")
    assert post.call_args.kwargs["json"]["input"] == "hola"
