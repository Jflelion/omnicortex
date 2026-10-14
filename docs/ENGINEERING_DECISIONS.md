<!-- markdownlint-disable MD024 -->

# OmniCortex Engineering Decisions

Este documento registra decisiones técnicas importantes y las razones detrás de ellas.

Cada decisión debe explicar:

- Contexto.
- Decisión tomada.
- Razones.
- Consecuencias.
- Alternativas consideradas.

---

## ADR-001 — FastAPI como framework backend

### Contexto

OmniCortex necesita una API moderna, rápida, tipada y compatible con procesamiento de IA.

### Decisión

Usar FastAPI como framework principal.

### Razones

- Soporte nativo para type hints.
- Documentación OpenAPI automática.
- Integración sencilla con Pydantic.
- Buen rendimiento.
- Adecuado para servicios de IA.

### Consecuencias

- Swagger disponible automáticamente.
- Los schemas se convierten en contratos claros de API.
- El sistema puede evolucionar hacia endpoints síncronos y asíncronos.

---

## ADR-002 — PostgreSQL como base de datos principal

### Contexto

El sistema necesita persistir usuarios, roles, documentos, chunks y vectores.

### Decisión

Usar PostgreSQL como base de datos relacional principal.

### Razones

- Base de datos madura.
- Buen soporte transaccional.
- Integración con SQLAlchemy.
- Compatibilidad con pgvector.
- Permite mantener datos relacionales y vectores en una sola plataforma.

### Alternativas consideradas

- MySQL.
- MongoDB.
- Supabase.
- Bases vectoriales independientes.

### Consecuencias

- Menor complejidad operativa.
- Una sola base mantiene metadata, relaciones y embeddings.
- Dependencia de PostgreSQL y pgvector.

---

## ADR-003 — Alembic para migraciones

### Contexto

La estructura de la base cambia conforme crece el producto.

### Decisión

Usar Alembic como única fuente de cambios de esquema.

### Razones

- Historial de cambios.
- Upgrades y downgrades.
- Integración con SQLAlchemy.
- Facilita despliegues reproducibles.

### Consecuencias

No se utilizará `Base.metadata.create_all()` como mecanismo principal de evolución del esquema.

---

## ADR-004 — Ollama para IA local

### Contexto

OmniCortex necesita embeddings y generación de respuestas sin depender inicialmente de servicios externos.

### Decisión

Usar Ollama como servidor local de modelos.

### Razones

- Privacidad.
- Ejecución local.
- Sin costo por llamada.
- Permite comprender la arquitectura completa.
- Facilita cambiar entre modelos.

### Consecuencias

- El rendimiento depende del equipo local.
- Los modelos pueden consumir RAM y CPU.
- Deben manejarse timeouts y disponibilidad del servicio.

---

## ADR-005 — `nomic-embed-text` para embeddings

### Contexto

Los chunks necesitan representación vectorial para búsqueda semántica.

### Decisión

Usar `nomic-embed-text`.

### Razones

- Disponible en Ollama.
- Adecuado para retrieval.
- Ejecución local.
- Produce vectores de 768 dimensiones.

### Consecuencias

La columna de pgvector debe ser:

```text
vector(768)

## ADR-006 — pgvector para almacenamiento vectorial

### Contexto

Los embeddings generados para cada chunk necesitan persistirse y consultarse mediante similitud vectorial.

### Decisión

Usar pgvector dentro de PostgreSQL.

### Razones

- Evita introducir una segunda base de datos.
- Mantiene metadata, relaciones y embeddings en el mismo sistema.
- Permite aplicar filtros de seguridad y propiedad directamente en SQL.
- Se integra con SQLAlchemy.
- Es suficiente para el volumen y la etapa actual de OmniCortex.

### Alternativas consideradas

- Pinecone.
- Weaviate.
- Qdrant.
- Chroma.
- Milvus.

### Consecuencias

- PostgreSQL administra datos relacionales y vectores.
- La dimensión configurada en pgvector debe coincidir exactamente con la del modelo de embeddings.
- Si el sistema escala considerablemente, podría evaluarse una base vectorial especializada.
- Cambiar de modelo de embeddings puede exigir modificar el esquema y regenerar vectores.

---

## ADR-007 — Arquitectura basada en servicios

### Contexto

La lógica de documentos, retrieval y generación comenzó a crecer dentro de los routers.

Mantenerla allí habría producido archivos extensos, alto acoplamiento y dificultades para probar cada componente de forma aislada.

### Decisión

Separar la lógica de aplicación en servicios con responsabilidades específicas.

### Servicios actuales

- `document_text_extractor.py`
- `text_chunker.py`
- `embedding_service.py`
- `retrieval_service.py`
- `reranker_service.py`
- `prompt_builder.py`
- `llm_service.py`
- `rag_service.py`

### Razones

- Aplicar el principio de responsabilidad única.
- Mantener los routers enfocados en HTTP.
- Facilitar pruebas unitarias.
- Reducir acoplamiento.
- Hacer reemplazables los proveedores de IA.
- Permitir que cada etapa del pipeline evolucione de forma independiente.

### Consecuencias

Los routers deben limitarse a:

```text
Recibir requests
Validar schemas
Resolver dependencias
Llamar servicios
Construir responses

## ADR-008 — Retrieval híbrido

### Contexto

La búsqueda semántica por embeddings no siempre posiciona primero los datos exactos.

Durante las pruebas, algunos chunks con contexto general sobre una persona aparecieron antes que chunks que contenían literalmente el dato solicitado, como un correo electrónico.

### Decisión

Combinar tres estrategias:

```text
Semantic search
+
Keyword search
+
Reranking

## ADR-008 — Retrieval híbrido

### Contexto

La búsqueda semántica por embeddings no siempre posiciona primero los datos exactos.

Durante las pruebas, algunos chunks con contexto general sobre una persona aparecieron antes que chunks que contenían literalmente el dato solicitado, como un correo electrónico.

### Decisión

Combinar tres estrategias:

```text
Semantic search
+
Keyword search
+
Reranking
Razones

La búsqueda semántica funciona bien para significado y paráfrasis.

La búsqueda por palabras clave funciona mejor para valores exactos como:

Nombres.
Correos.
Cédulas.
Teléfonos.
Fechas.
Códigos.
Números de contrato.
Referencias específicas.

El reranking permite reordenar los candidatos según la pregunta concreta.

Consecuencias
Mejora la precisión del retrieval.
Aumenta la complejidad del pipeline.
El sistema debe distinguir entre distancia semántica y score final.
Las reglas específicas actuales deberán evolucionar hacia análisis de intención, entidades y expansión de consultas.
El retrieval debe seguir respetando la propiedad de los documentos del usuario autenticado.
ADR-009 — Respuestas RAG con fuentes auditables
Contexto

Una respuesta generada por un LLM sin evidencia visible es difícil de validar, depurar y auditar.

Decisión

El endpoint:

POST /documents/ask

debe devolver:

answer
sources

Cada fuente debe incluir, cuando corresponda:

chunk_id
document_id
chunk_index
content
distance
score
Razones
Permite verificar de dónde salió la respuesta.
Mejora la confianza del usuario.
Facilita depuración del retrieval.
Hace posible comparar ranking semántico y ranking final.
Permite evaluar la calidad del sistema RAG.
Reduce el riesgo de respuestas sin respaldo documental.
Consecuencias
Las respuestas de la API son más extensas.
Debe controlarse cuánto contenido de cada chunk se expone.
En producción podrían devolverse extractos en lugar del contenido completo.
Las fuentes deben pertenecer únicamente al usuario autorizado.
La respuesta generada y la evidencia recuperada deben conservar trazabilidad.
ADR-010 — Observabilidad propia antes de herramientas externas
Contexto

El pipeline de IA necesita registrar qué ocurrió, cuánto tardó cada etapa y dónde se produjo un error.

Herramientas como OpenTelemetry, Datadog, LangSmith o sistemas APM podrían resolver parte de esta necesidad, pero introducirlas ahora agregaría complejidad antes de comprender los fundamentos.

Decisión

Crear primero una capa propia de observabilidad:

app/observability/
├── __init__.py
├── logger.py
├── timers.py
├── metrics.py
└── tracing.py
Responsabilidades
logger.py
Configurar logging.
Crear loggers por módulo.
Registrar eventos, advertencias y errores.
timers.py
Medir duración de procesos.
Registrar tiempos en milisegundos.
Utilizar un reloj monotónico de alta precisión.
metrics.py
Contabilizar eventos.
Registrar cantidades procesadas.
Preparar métricas internas.
tracing.py
Asociar etapas de una misma petición.
Incorporar correlation IDs.
Seguir el recorrido completo de una operación.
Razones
Comprender cómo funciona la observabilidad.
Mantener baja la complejidad inicial.
Poder medir extracción, embeddings, retrieval, reranking y generación.
Preparar una futura integración con herramientas externas.
Evitar depender prematuramente de un proveedor.
Consecuencias
La primera implementación será sencilla y local.
No sustituirá permanentemente una solución APM completa.
La arquitectura debe permitir reemplazarla o integrarla después con:
OpenTelemetry.
Datadog.
Prometheus.
Grafana.
LangSmith.
Sentry.
Los servicios importantes deberán usar logging y temporizadores consistentes.

---

## ADR-011 — Contexto conversacional sin reescritura de la pregunta

### Contexto

En una conversación, las preguntas de seguimiento ("¿y su teléfono?") no contienen las palabras necesarias para recuperar los chunks correctos.

### Decisión

- El prompt incluye los últimos `CONVERSATION_HISTORY_MESSAGES` mensajes.
- La consulta de retrieval y reranking concatena la pregunta anterior del usuario con la actual.
- La pregunta y la respuesta se guardan juntas solo cuando la respuesta se genera; si Ollama falla, la conversación no cambia.
- Las fuentes se guardan como JSON en el mensaje, para que la respuesta siga siendo auditable aunque el documento se elimine.

### Alternativas consideradas

- Reescribir la pregunta con el LLM (standalone question). Da mejores consultas, pero añade una segunda llamada al modelo por turno, lo que con `qwen2.5:3b` en local duplica la latencia.

### Consecuencias

- Cero llamadas extra al modelo por turno.
- La consulta de retrieval es más ruidosa cuando el usuario cambia de tema; se puede sustituir por reescritura con LLM sin cambiar la API.

---

## ADR-012 — Proveedores de IA intercambiables para la demo pública

### Contexto

En local, OmniCortex usa Ollama. Una demo pública con Ollama necesitaría un servidor con GPU, demasiado caro para un proyecto de portafolio.

### Decisión

- `LLM_PROVIDER`: `ollama` (local) o `anthropic` (Claude Haiku 5.5 con esfuerzo `low`).
- `EMBEDDING_PROVIDER`: `ollama` o `nomic` (API hospedada de Nomic con `nomic-embed-text-v1.5`).
- Ambos clientes devuelven las mismas estructuras y convierten los fallos del proveedor en `AIServiceUnavailableError` (HTTP 503), así que el pipeline RAG no cambia.
- Con Nomic, los chunks se embeben con `search_document` y las consultas con `search_query`, por lotes de 32.

### Alternativas consideradas

- Embeddings dentro del contenedor con `fastembed` (mismo modelo cuantizado). Medido: 412 MB de pico frente a 512 MB disponibles en el plan de Render; con Nomic la API ocupa unos 175 MB.
- Otros modelos de embeddings hospedados (p. ej. Voyage): no ofrecen 768 dimensiones, lo que obligaría a migrar la columna `vector(768)`.

### Consecuencias

- Mismo esquema y dimensiones en local y en la demo.
- `/health` solo consulta Ollama si algún proveedor lo usa; los proveedores hospedados no se llaman en el health check porque cada llamada cuesta.
- La configuración se niega a arrancar si falta la clave del proveedor elegido.

