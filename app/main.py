from fastapi import FastAPI
from app.observability.logger import configure_logging
from app.routers import auth, documents, roles, users
from app.observability.request_id_middleware import RequestIdMiddleware

configure_logging()

app = FastAPI(
    title="OmniCortex API",
    description="Backend para una plataforma de inteligencia documental y RAG.",
    version="1.0.0"
)


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(roles.router)
app.include_router(documents.router)
app.add_middleware(RequestIdMiddleware)

@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "OmniCortex API is running"
    }