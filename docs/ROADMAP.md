
# 3. Crear `ROADMAP.md`

```markdown
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
- [ ] Medir retrieval.
- [ ] Medir reranking.
- [ ] Medir prompt building.
- [ ] Medir generación LLM.
- [ ] Medir tiempo total.
- [ ] Correlation ID.
- [ ] Métricas básicas.

### Configuración

- [ ] Mover modelos Ollama a `.env`.
- [ ] Mover URLs a `.env`.
- [ ] Configurar chunk size.
- [ ] Configurar overlap.
- [ ] Configurar top-k.
- [ ] Configurar timeouts.

### Error Handling

- [ ] Errores de Ollama.
- [ ] Timeouts.
- [ ] Errores de extracción.
- [ ] Errores de embeddings.
- [ ] Respuestas HTTP estructuradas.

### Testing

- [ ] Configurar pytest.
- [ ] Tests del chunker.
- [ ] Tests del reranker.
- [ ] Tests del prompt builder.
- [ ] Tests de autenticación.
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

- Conversaciones.
- Mensajes.
- Historial.
- Memoria.
- Contexto conversacional.
- Títulos automáticos.
- Resumen de conversaciones.

---

## Fase 7 — Processing Infrastructure

- Background jobs.
- Redis.
- Workers.
- Estados de procesamiento.
- Reintentos.
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

- Next.js.
- Login.
- Dashboard.
- Upload.
- Chat.
- Fuentes visuales.
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

- CI/CD.
- Deployment.
- Secrets management.
- Rate limiting.
- Backups.
- Monitoring.
- OpenTelemetry.
- Seguridad avanzada.
- Evaluaciones continuas
