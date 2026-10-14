<!-- markdownlint-disable MD024 -->

# Changelog

Todos los cambios importantes de OmniCortex serán documentados en este archivo.

El formato se inspira en Keep a Changelog y el proyecto seguirá versionado semántico cuando se publiquen versiones estables.

---

## [Unreleased]

### En desarrollo

- Sistema profesional de observabilidad.
- Logging centralizado.
- Medición de tiempos del pipeline RAG.
- Manejo estructurado de errores.
- Configuración centralizada.
- Arquitectura de proveedores de IA.
- Pruebas automatizadas.

### Added

- Estado de procesamiento en documentos (`processing`, `ready`, `failed`) y `error_message`.
- `POST /documents/{id}/reindex` para reintentar documentos fallidos.
- Conversaciones (`/conversations`) con historial persistente, contexto de los últimos `CONVERSATION_HISTORY_MESSAGES` mensajes y título automático.
- Las fuentes de cada respuesta se guardan con el mensaje e incluyen el nombre del archivo.
- Frontend React + TypeScript (`frontend/`): login, documentos con estado en vivo, chat con historial y fuentes.
- Servicio `web` en docker-compose (nginx + build de React, proxy `/api`).
- CI con GitHub Actions.
- Proveedores de IA intercambiables: Claude Haiku (`LLM_PROVIDER=anthropic`) y embeddings de Nomic (`EMBEDDING_PROVIDER=nomic`).
- Blueprint de Render (`render.yaml`) y guía `docs/DEPLOY.md`; la API respeta `PORT`.
- Aviso en el login mientras el servidor de la demo despierta.
- Capturas de pantalla en el README.
- Validación de `question` (1–2000 caracteres) y `limit` (1–20) en las preguntas.
- Borrado en cascada (`ON DELETE CASCADE`) de usuario → documentos → chunks; los archivos subidos también se eliminan.

### Changed

- Las respuestas de documentos ya no exponen la ruta interna del archivo (`filepath`).
- La migración `b65734e48ae9` crea la columna `embedding` si no existe: una base de datos nueva ya puede migrar desde cero.
- `embed_chunks` actualiza el estado de cada documento que procesa.

---

## [0.4.0] — Engineering Excellence Sprint

### Added

- Nueva capa `app/observability`.
- Configuración centralizada de logging.
- Clase `Timer` basada en `perf_counter`.
- Documentación arquitectónica del sistema.
- Estrategia de documentación mediante:
  - `README.md`
  - `ARCHITECTURE.md`
  - `CHANGELOG.md`
  - `ENGINEERING_DECISIONS.md`
  - `ROADMAP.md`

### Changed

- Se detuvo temporalmente la creación de funcionalidades nuevas.
- El proyecto entra en una fase de consolidación arquitectónica.
- Se adopta documentación mediante docstrings para servicios, seguridad, procesamiento documental y pipeline de IA.

### Goals

- Mejorar mantenibilidad.
- Reducir deuda técnica.
- Medir rendimiento.
- Preparar la plataforma para crecimiento futuro.
- Convertir OmniCortex en una plataforma de IA mantenible.

---

## [0.3.0] — Local RAG Engine

### Added

- Upload de documentos PDF.
- Almacenamiento físico de archivos.
- Modelo `Document`.
- Relación entre usuarios y documentos.
- Extracción de texto mediante PyMuPDF.
- Campo `extracted_text`.
- Chunking con overlap.
- Modelo `DocumentChunk`.
- Persistencia de chunks en PostgreSQL.
- Extensión pgvector.
- Embeddings locales con Ollama.
- Modelo `nomic-embed-text`.
- Vectores de 768 dimensiones.
- Búsqueda semántica.
- Búsqueda híbrida por embeddings y palabras clave.
- Reranking de resultados.
- LLM local con `qwen2.5:3b`.
- Endpoint RAG `/documents/ask`.
- Respuestas acompañadas de fuentes.
- Score explicable para resultados recuperados.

### Changed

- El retrieval pasó de búsqueda exclusivamente semántica a recuperación híbrida.
- La lógica RAG se dividió en servicios especializados:
  - `retrieval_service.py`
  - `reranker_service.py`
  - `prompt_builder.py`
  - `llm_service.py`
  - `rag_service.py`
- El modelo generador se cambió de `llama3.1:8b` a `qwen2.5:3b` durante desarrollo para reducir tiempos de respuesta.

### Lessons Learned

- La dimensión del embedding debe coincidir exactamente con la dimensión de pgvector.
- Los modelos locales grandes pueden provocar timeouts.
- El retrieval debe validarse antes de integrar un LLM.
- Una respuesta RAG debe incluir evidencia auditable.
- La búsqueda semántica no reemplaza completamente la búsqueda textual.
- El reranking mejora significativamente la calidad de las fuentes.

---

## [0.2.0] — Document Intelligence

### Added

- Modelo de documentos.
- Migraciones Alembic para documentos.
- Upload protegido con JWT.
- Asociación de documentos al usuario autenticado.
- Extracción automática de texto PDF.
- Endpoints:
  - `POST /documents/upload`
  - `GET /documents/`
  - `GET /documents/{document_id}`
  - `GET /documents/{document_id}/chunks`

---

## [0.1.0] — Backend Foundation

### Added

- FastAPI.
- PostgreSQL en Docker.
- SQLAlchemy ORM.
- Alembic.
- Configuración mediante `.env`.
- Usuarios y roles.
- Hashing de contraseñas.
- Autenticación JWT.
- Autorización RBAC.
- Endpoints protegidos.
- Soft delete y hard delete de usuarios.
- Seed para roles iniciales.
- DBeaver como herramienta visual de base de datos.
