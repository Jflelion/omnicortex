# OmniCortex Roadmap

## Visión

Convertir OmniCortex en una plataforma de inteligencia y recuperación de conocimiento capaz de procesar múltiples fuentes, encontrar evidencia relevante y generar respuestas auditables.

---

## Fase 1 — Backend Foundation

Estado: completada.

- FastAPI.
- PostgreSQL.
- Docker.
- SQLAlchemy.
- Alembic.
- Configuración `.env`.
- JWT.
- RBAC.
- Usuarios.
- Roles.
- Soft delete.
- Hard delete.

---

## Fase 2 — Document Intelligence

Estado: completada.

- Upload PDF.
- Metadata.
- Storage local.
- Extracción de texto.
- Relación usuario-documento.
- Chunking.
- Overlap.
- Persistencia de chunks.

---

## Fase 3 — Local RAG Engine

Estado: completada.

- Ollama.
- Embeddings locales.
- `nomic-embed-text`.
- pgvector.
- Semantic search.
- Keyword search.
- Hybrid retrieval.
- Reranking.
- Prompt builder.
- LLM local.
- `qwen2.5:3b`.
- Endpoint `/documents/ask`.
- Fuentes auditables.

---

## Fase 4 — Engineering Excellence

Estado: en desarrollo.

### Observabilidad

- [x] Crear capa `app/observability`.
- [x] Configuración base de logging.
- [x] Clase Timer.
- [x] Medir retrieval.
- [x] Medir reranking.
- [x] Medir prompt building.
- [x] Medir generación LLM.
- [x] Medir tiempo total.
- [x] Correlation ID.
- [ ] Métricas básicas.

### Configuración

- [x] Mover modelos Ollama a `.env`.
- [x] Mover URLs a `.env`.
- [x] Configurar chunk size.
- [x] Configurar overlap.
- [ ] Configurar top-k.
- [x] Configurar timeouts.

### Error Handling

- [x] Errores de Ollama.
- [x] Timeouts.
- [x] Errores de extracción.
- [x] Errores de embeddings.
- [ ] Respuestas HTTP estructuradas.

### Testing

- [x] Configurar pytest.
- [x] Tests del chunker.
- [x] Tests del reranker.
- [x] Tests del prompt builder.
- [x] Tests de autenticación.
- [ ] Tests de integración RAG.

---

## Fase 5 — Retrieval Quality

- Query analyzer.
- Query expansion.
- Intent detection.
- Entity extraction.
- Metadata filters.
- Filtro por documento.
- Threshold de relevancia.
- Score explicable.
- Evaluación automática de retrieval.
- Reranker basado en modelo.

---

## Fase 6 — Conversational RAG

Estado: en desarrollo.

- [x] Conversaciones.
- [x] Mensajes.
- [x] Historial.
- [ ] Memoria.
- [x] Contexto conversacional (últimos N mensajes en el prompt y en la consulta de retrieval).
- [x] Títulos automáticos (a partir de la primera pregunta).
- [ ] Resumen de conversaciones.
- [ ] Reescritura de la pregunta con el LLM.

---

## Fase 7 — Processing Infrastructure

- Background jobs.
- Redis.
- Workers.
- [x] Estados de procesamiento.
- [x] Reintentos (manual, `POST /documents/{id}/reindex`).
- Procesamiento por lotes.
- Cola de embeddings.
- Indexación asíncrona.

---

## Fase 8 — Multitenancy

- Organizations.
- Workspaces.
- Memberships.
- Permisos avanzados.
- Colecciones.
- Documentos compartidos.
- API keys.

---

## Fase 9 — Multimodal Knowledge

- DOCX.
- TXT.
- Excel.
- OCR.
- Imágenes.
- Audio.
- Video.
- Emails.
- APIs.
- Bases de datos.

---

## Fase 10 — Frontend

Estado: en desarrollo (React + Vite en lugar de Next.js: no hace falta SSR para una app autenticada).

- [x] Login y registro.
- [x] Upload con estado de procesamiento.
- [x] Chat con historial.
- [x] Fuentes visuales.
- Administración de usuarios.
- Administración de documentos.
- Métricas y observabilidad.

---

## Fase 11 — AI Agents

- Tool calling.
- Agent orchestration.
- Connectors.
- Acciones sobre sistemas externos.
- Flujos multiagente.
- Human-in-the-loop.

---

## Fase 12 — Production Readiness

- [x] CI (tests, migraciones, lint, build, imágenes Docker).
- CD.
- Deployment.
- Secrets management.
- Rate limiting.
- Backups.
- Monitoring.
- OpenTelemetry.
- Seguridad avanzada.
- Evaluaciones continuas
