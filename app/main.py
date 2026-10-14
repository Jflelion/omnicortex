from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AIServiceUnavailableError
from app.observability.logger import configure_logging
from app.routers import auth, conversations, documents, health, roles, users
from app.observability.request_id_middleware import RequestIdMiddleware

configure_logging()

app = FastAPI(
    title="OmniCortex API",
    description="Backend para una plataforma de inteligencia documental y RAG.",
    version="1.0.0"
)


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(roles.router)
app.include_router(documents.router)
app.include_router(conversations.router)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AIServiceUnavailableError)
def ai_service_unavailable_handler(
    request: Request,
    exc: AIServiceUnavailableError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": (
                f"{exc}. Check that Ollama is running and try again."
                if "ollama" in (settings.LLM_PROVIDER, settings.EMBEDDING_PROVIDER)
                else f"{exc}. Please try again in a moment."
            )
        }
    )


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "OmniCortex API is running"
    }