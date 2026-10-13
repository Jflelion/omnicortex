Perfecto. Documentemos de forma profesional, no línea por línea.

Crea o actualiza:

```text
README.md
```

con esta estructura:

````markdown
# OmniCortex Backend

OmniCortex is a backend foundation for an AI SaaS platform built with FastAPI, PostgreSQL, Docker, SQLAlchemy, Alembic, JWT authentication, and role-based authorization.

## Current Stack

- FastAPI
- PostgreSQL
- Docker
- SQLAlchemy
- Alembic
- Pydantic
- PyJWT
- Passlib + bcrypt
- DBeaver

## Current Features

- PostgreSQL database running in Docker
- SQLAlchemy ORM models
- Alembic migrations
- Environment-based configuration with `.env`
- Users and roles
- Password hashing
- JWT login
- Protected routes
- Role-based authorization
- Soft delete and hard delete for users
- Seed script for default roles

## Project Structure

```text
omnicortex/
├── app/
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── jwt_handler.py
│   │   └── permissions.py
│   ├── database/
│   │   ├── database.py
│   │   └── seed.py
│   ├── models/
│   │   ├── role.py
│   │   └── user.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── roles.py
│   │   └── users.py
│   ├── schemas/
│   │   ├── role.py
│   │   └── user.py
│   └── main.py
├── alembic/
├── alembic.ini
├── docker-compose.yml
├── requirements.txt
├── .env
└── README.md
````

## Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://admin:admin123@localhost:5432/omnicortex_db
SECRET_KEY=your_secure_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Running PostgreSQL

```powershell
docker compose up -d
```

Check the container:

```powershell
docker ps
```

## Running Migrations

```powershell
alembic upgrade head
```

Create a new migration:

```powershell
alembic revision --autogenerate -m "migration message"
```

## Seeding Default Roles

```powershell
python -m app.database.seed
```

Default roles:

* admin
* user
* analyst

## Running the API

```powershell
python -m uvicorn app.main:app --reload
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

## Authentication Flow

1. Create roles using the seed script.
2. Create an admin user.
3. Login using `/auth/login`.
4. Copy the JWT access token.
5. Use Swagger `Authorize`.
6. Access protected routes.

## Authorization

OmniCortex currently uses role-based authorization.

Example:

```python
Depends(require_roles(["admin"]))
```

Protected admin routes include:

* `GET /users/`
* `POST /roles/`
* user update/deactivate/delete operations

## Current API Modules

### Auth

* `POST /auth/login`
* `GET /auth/me`

### Users

* `POST /users/`
* `GET /users/`
* `GET /users/{user_id}`
* `PUT /users/{user_id}`
* `PATCH /users/{user_id}/deactivate`
* `PATCH /users/{user_id}/activate`
* `DELETE /users/{user_id}`

### Roles

* `POST /roles/`
* `GET /roles/`

## Development Notes

* `.env` must be in the project root, not inside `venv`.
* PostgreSQL must be running before starting the API.
* Alembic now controls database schema changes.
* Do not use `Base.metadata.create_all()` in `main.py`.
* `users` and `roles` are managed through SQLAlchemy ORM models.

## Roadmap

### Phase 1 — Backend Foundation

* Docker + PostgreSQL
* FastAPI
* SQLAlchemy
* Alembic
* JWT Auth
* Role authorization

### Phase 2 — Document System

* Document model
* File upload
* User-document relationship
* File metadata
* Local storage

### Phase 3 — AI Layer

* Text extraction
* Chunking
* Embeddings
* Vector search
* RAG
* Chat with documents

### Phase 4 — Advanced Architecture

* Service layer
* Repository layer
* Background tasks
* Logging
* Testing
* Redis / workers

### Phase 5 — Frontend

* Next.js dashboard
* Login UI
* Document upload UI
* Chat interface
* Admin panel

```

Después de guardar el README, seguimos con **Documents Module**.
```
