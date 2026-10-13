import fitz  # pyright: ignore[reportMissingTypeStubs]
import pytest

from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.routers import documents
from tests.conftest import auth_headers


@pytest.fixture(autouse=True)
def isolated_uploads(tmp_path, monkeypatch):
    monkeypatch.setattr(documents, "UPLOAD_DIR", tmp_path)

    # Embedding runs against Ollama in a separate session; not under test here.
    indexed: list[int] = []
    monkeypatch.setattr(
        documents,
        "index_document_in_background",
        indexed.append
    )

    return tmp_path, indexed


def make_pdf(text: str) -> bytes:
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), text)
    data = pdf.tobytes()
    pdf.close()

    return data


def upload(client, headers, filename: str, data: bytes):
    return client.post(
        "/documents/upload",
        files={"file": (filename, data, "application/pdf")},
        headers=headers
    )


def test_upload_pdf_stores_document_and_chunks(client, db, create_user, isolated_uploads):
    upload_dir, indexed = isolated_uploads
    user = create_user("alice")

    response = upload(client, auth_headers(user), "informe.pdf", make_pdf("Hola OmniCortex"))

    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "informe.pdf"

    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == body["id"]).all()
    assert len(chunks) == 1
    assert "Hola OmniCortex" in chunks[0].content
    assert indexed == [body["id"]]
    assert len(list(upload_dir.iterdir())) == 1


@pytest.mark.parametrize(
    ("filename", "data", "expected_status"),
    [
        ("notas.txt", b"%PDF-1.7 fake", 415),
        ("falso.pdf", b"esto no es un pdf", 415),
        ("vacio.pdf", b"", 400),
        ("roto.pdf", b"%PDF-1.7 contenido corrupto", 400),
    ]
)
def test_upload_rejects_invalid_files(
    client, create_user, isolated_uploads, filename, data, expected_status
):
    upload_dir, indexed = isolated_uploads
    user = create_user("alice")

    response = upload(client, auth_headers(user), filename, data)

    assert response.status_code == expected_status
    assert list(upload_dir.iterdir()) == []
    assert indexed == []


def test_upload_rejects_files_over_size_limit(client, create_user, isolated_uploads, monkeypatch):
    upload_dir, _ = isolated_uploads
    monkeypatch.setattr(documents, "MAX_UPLOAD_SIZE_BYTES", 100)
    user = create_user("alice")

    response = upload(client, auth_headers(user), "grande.pdf", make_pdf("x" * 50))

    assert response.status_code == 413
    assert list(upload_dir.iterdir()) == []


def test_upload_requires_authentication(client):
    assert upload(client, {}, "a.pdf", make_pdf("hola")).status_code == 401


def test_delete_document_removes_record_chunks_and_file(client, db, create_user, isolated_uploads):
    upload_dir, _ = isolated_uploads
    user = create_user("alice")
    headers = auth_headers(user)

    document_id = upload(client, headers, "a.pdf", make_pdf("Hola")).json()["id"]

    response = client.delete(f"/documents/{document_id}", headers=headers)

    assert response.status_code == 204
    assert db.get(Document, document_id) is None
    assert db.query(DocumentChunk).count() == 0
    assert list(upload_dir.iterdir()) == []


def test_cannot_access_or_delete_other_users_documents(client, db, create_user):
    owner = create_user("alice")
    intruder = create_user("mallory")

    document_id = upload(client, auth_headers(owner), "a.pdf", make_pdf("Hola")).json()["id"]
    intruder_headers = auth_headers(intruder)

    assert client.get(f"/documents/{document_id}", headers=intruder_headers).status_code == 404
    assert client.delete(f"/documents/{document_id}", headers=intruder_headers).status_code == 404
    assert db.get(Document, document_id) is not None


def test_upload_response_exposes_status_but_not_internal_path(client, create_user):
    user = create_user("alice")

    body = upload(client, auth_headers(user), "a.pdf", make_pdf("Hola")).json()

    assert body["status"] == "processing"
    assert body["error_message"] is None
    assert "filepath" not in body


def test_upload_pdf_without_text_is_marked_failed(client, create_user, isolated_uploads):
    _, indexed = isolated_uploads
    user = create_user("alice")

    response = upload(client, auth_headers(user), "escaneado.pdf", make_pdf(""))

    assert response.status_code == 201
    assert response.json()["status"] == "failed"
    assert response.json()["error_message"]
    assert indexed == []


def test_reindex_failed_document_queues_indexing(client, db, create_user, isolated_uploads):
    _, indexed = isolated_uploads
    user = create_user("alice")
    headers = auth_headers(user)

    document_id = upload(client, headers, "a.pdf", make_pdf("Hola")).json()["id"]
    document = db.get(Document, document_id)
    document.status = DocumentStatus.FAILED
    document.error_message = "boom"
    db.commit()

    response = client.post(f"/documents/{document_id}/reindex", headers=headers)

    assert response.status_code == 202
    assert response.json()["status"] == "processing"
    assert response.json()["error_message"] is None
    assert indexed == [document_id, document_id]


def test_reindex_rejects_documents_not_failed(client, create_user):
    user = create_user("alice")
    headers = auth_headers(user)

    document_id = upload(client, headers, "a.pdf", make_pdf("Hola")).json()["id"]

    response = client.post(f"/documents/{document_id}/reindex", headers=headers)

    assert response.status_code == 409


def test_reindex_rejects_documents_without_text(client, create_user):
    user = create_user("alice")
    headers = auth_headers(user)

    document_id = upload(client, headers, "a.pdf", make_pdf("")).json()["id"]

    response = client.post(f"/documents/{document_id}/reindex", headers=headers)

    assert response.status_code == 422


def test_deleting_user_cascades_to_documents_chunks_and_files(
    client, db, create_user, isolated_uploads
):
    upload_dir, _ = isolated_uploads
    owner = create_user("alice")
    admin = create_user("root", role_name="admin")

    upload(client, auth_headers(owner), "a.pdf", make_pdf("Hola"))
    upload(client, auth_headers(owner), "b.pdf", make_pdf("Adios"))

    response = client.delete(f"/users/{owner.id}", headers=auth_headers(admin))

    assert response.status_code == 204
    db.expire_all()
    assert db.query(Document).count() == 0
    assert db.query(DocumentChunk).count() == 0
    assert list(upload_dir.iterdir()) == []
