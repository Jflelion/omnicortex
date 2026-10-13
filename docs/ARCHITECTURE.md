# OmniCortex Architecture

## 1. Objetivo del sistema

OmniCortex será una plataforma de inteligencia documental capaz de:

```text
Recibir información
↓
Procesarla
↓
Convertirla en conocimiento consultable
↓
Recuperar evidencia relevante
↓
Generar respuestas fundamentadas
```

No será solamente un chatbot sobre archivos PDF.

La arquitectura debe permitir soportar en el futuro:

- PDF
- DOCX
- TXT
- Excel
- Imágenes con OCR
- Audio transcrito
- Video transcrito
- Correos electrónicos
- APIs externas
- Bases de datos
- Sensores y fuentes operativas

---

## 2. Vista general de la arquitectura

```text
┌──────────────────────────────────────────────────────┐
│                    CLIENT LAYER                      │
│                                                      │
│  Swagger / Frontend / Mobile / Integraciones API    │
└─────────────────────────┬────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────┐
│                     API LAYER                        │
│                                                      │
│  Auth Router                                         │
│  Users Router                                        │
│  Roles Router                                        │
│  Documents Router                                    │
│  Search Router — futuro                              │
│  Conversations Router — futuro                       │
└─────────────────────────┬────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────┐
│                APPLICATION SERVICES                  │
│                                                      │
│  Document Service                                    │
│  Retrieval Service                                   │
│  Reranker Service                                    │
│  Prompt Builder                                      │
│  RAG Service                                         │
│  LLM Service                                         │
└─────────────────────────┬────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────┐
│                   AI PIPELINE                        │
│                                                      │
│  Query Analysis                                      │
│  Query Expansion                                     │
│  Semantic Retrieval                                  │
│  Keyword Retrieval                                   │
│  Fusion                                              │
│  Reranking                                           │
│  Context Building                                    │
│  Generation                                          │
└─────────────────────────┬────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────┐
│                  DATA & STORAGE                      │
│                                                      │
│  PostgreSQL                                          │
│  pgvector                                            │
│  File Storage                                        │
│  Ollama                                              │
└──────────────────────────────────────────────────────┘
```

---

## 3. Pipelines principales

OmniCortex tiene dos pipelines principales:

1. Pipeline de ingesta de conocimiento.
2. Pipeline de consulta de conocimiento.

---

## 3.1 Pipeline de ingesta de conocimiento

Este pipeline se ejecuta cuando un usuario sube un documento.

```text
Archivo
↓
Validación
↓
Almacenamiento físico
↓
Extracción de contenido
↓
Normalización
↓
Chunking
↓
Embeddings
↓
Persistencia en pgvector
↓
Documento listo para búsqueda
```

### Componentes actuales

```text
documents.py
document_text_extractor.py
text_chunker.py
embedding_service.py
Document
DocumentChunk
PostgreSQL
pgvector
```

### Estado actual

```text
PDF                  ✅
Extracción de texto  ✅
Chunking             ✅
Embeddings           ✅
Persistencia vector  ✅
```

---

## 3.2 Pipeline de consulta de conocimiento

Este pipeline se ejecuta cuando el usuario hace una pregunta.

```text
Pregunta
↓
Análisis de consulta
↓
Expansión de consulta
↓
Recuperación semántica
↓
Recuperación por palabras clave
↓
Fusión de candidatos
↓
Reranking
↓
Selección de evidencia
↓
Construcción del prompt
↓
LLM
↓
Respuesta + fuentes
```

### Componentes actuales services

```text
embedding_service.py
retrieval_service.py
reranker_service.py
prompt_builder.py
llm_service.py
rag_service.py
```

### Estado actual Procesal

```text
Semantic search        ✅
Keyword retrieval      ✅
Hybrid retrieval       ✅
Reranking              ✅
Prompt building        ✅
LLM local              ✅
Respuesta con fuentes  ✅
```

---

## 4. Responsabilidad de cada capa

## 4.1 Routers

Los routers deben encargarse únicamente de la capa HTTP.

Responsabilidades:

```text
Recibir request
Validar schema
Resolver dependencias
Llamar servicios
Construir response
```

No deben contener:

```text
Extracción de PDF
Chunking
Embeddings
Reranking
Construcción de prompts
Lógica compleja de base de datos
```

Ejemplo ideal:

```python
@router.post("/ask", response_model=AskResponse)
def ask_documents(...):
    result = rag_service.ask(...)
    return result
```

---

## 4.2 Models

Los models representan tablas y relaciones de PostgreSQL.

Modelos actuales:

```text
User
Role
Document
DocumentChunk
```

Los models no deben:

- Procesar PDFs.
- Generar embeddings.
- Llamar modelos de IA.
- Construir prompts.
- Contener lógica de negocio compleja.

---

## 4.3 Schemas

Los schemas definen los contratos de entrada y salida de la API.

Schemas actuales:

```text
UserCreate
UserUpdate
UserResponse
RoleCreate
RoleResponse
DocumentResponse
DocumentChunkResponse
SearchRequest
SearchResult
AskRequest
AskResponse
AskSource
```

Su responsabilidad es controlar:

```text
Qué datos entran
Qué datos salen
Cómo se validan
Cómo aparecen en Swagger
```

---

## 4.4 Services

Los services contienen la lógica de aplicación.

### `document_text_extractor.py`

Responsabilidad:

```text
Archivo PDF → texto
```

---

### `text_chunker.py`

Responsabilidad:

```text
Texto → fragmentos
```

---

### `embedding_service.py`

Responsabilidad:

```text
Texto → vector de 768 dimensiones
```

Actualmente utiliza:

```text
Ollama
nomic-embed-text
```

---

### `retrieval_service.py`

Responsabilidad:

```text
Pregunta → candidatos relevantes
```

Combina:

```text
Búsqueda semántica
+
Búsqueda por palabras clave
```

No debe generar respuestas.

---

### `reranker_service.py`

Responsabilidad:

```text
Candidatos → candidatos reordenados
```

Evalúa qué fragmentos tienen mayor probabilidad de responder la pregunta.

Actualmente utiliza:

```text
Distancia semántica
Coincidencias de palabras clave
Detección de patrones
Score final
```

---

### `prompt_builder.py`

Responsabilidad:

```text
Pregunta + evidencia → prompt final
```

Debe:

- Organizar los chunks.
- Delimitar el contexto.
- Incluir instrucciones al modelo.
- Evitar respuestas basadas en información externa.
- Indicar qué hacer cuando la respuesta no existe.

---

### `llm_service.py`

Responsabilidad:

```text
Prompt → respuesta del modelo
```

Actualmente utiliza:

```text
Ollama
qwen2.5:3b
```

El servicio debe permanecer desacoplado para permitir cambiar de proveedor.

---

### `rag_service.py`

Responsabilidad:

```text
Coordinar el pipeline RAG
```

Flujo:

```text
Pregunta
↓
Retrieval
↓
Reranking
↓
Prompt Builder
↓
LLM
↓
Respuesta + fuentes
```

Este servicio no debe implementar directamente:

- SQL.
- Embeddings.
- Llamadas HTTP a Ollama.
- Reglas internas del reranker.
- Extracción de texto.

---

## 5. Arquitectura futura del módulo de IA

La carpeta `services` es suficiente para el tamaño actual.

Cuando OmniCortex crezca, la arquitectura objetivo será:

```text
app/
├── ai/
│   ├── ingestion/
│   │   ├── extractors/
│   │   ├── chunkers/
│   │   ├── normalizers/
│   │   └── ingestion_service.py
│   │
│   ├── retrieval/
│   │   ├── query_analyzer.py
│   │   ├── query_expander.py
│   │   ├── semantic_retriever.py
│   │   ├── keyword_retriever.py
│   │   ├── hybrid_retriever.py
│   │   └── reranker.py
│   │
│   ├── generation/
│   │   ├── prompt_builder.py
│   │   ├── rag_service.py
│   │   └── response_builder.py
│   │
│   └── providers/
│       ├── ollama_embedding_provider.py
│       ├── ollama_llm_provider.py
│       ├── openai_embedding_provider.py
│       ├── openai_llm_provider.py
│       ├── anthropic_llm_provider.py
│       └── gemini_llm_provider.py
```

Esta migración no se hará todavía para evitar sobreingeniería.

Se conserva como arquitectura objetivo.

---

## 6. Interfaces de proveedores

Actualmente OmniCortex depende directamente de Ollama.

En el futuro debe soportar múltiples proveedores.

### Embedding providers

```text
Embedding Provider
├── Ollama
├── OpenAI
├── Azure OpenAI
├── Cohere
└── Hugging Face
```

### LLM providers

```text
LLM Provider
├── Ollama
├── OpenAI
├── Anthropic
├── Gemini
└── Azure OpenAI
```

La aplicación no debería saber qué proveedor está activo.

Uso ideal:

```python
embedding_provider.generate(text)
```

```python
llm_provider.generate(prompt)
```

Cambiar de proveedor no debe obligar a modificar el pipeline RAG.

---

## 7. Seguridad y aislamiento de datos

La seguridad actual utiliza:

```text
JWT
RBAC
User ownership
```

Cada consulta documental debe respetar:

```python
Document.owner_id == current_user.id
```

La búsqueda semántica y vectorial nunca debe recuperar chunks pertenecientes a otro usuario.

Esto representa una primera versión de arquitectura multitenant.

Evolución futura:

```text
Organization
Workspace
Membership
Document permissions
Shared collections
Teams
API keys
```

---

## 8. Observabilidad

Todo pipeline de IA debe poder inspeccionarse.

OmniCortex debe poder registrar:

```text
Pregunta original
Consulta expandida
Entidades detectadas
Intención detectada
Chunks candidatos
Distancia semántica
Coincidencias por keywords
Score del reranker
Chunks enviados al LLM
Modelo utilizado
Tiempo de retrieval
Tiempo de generación
Respuesta final
Errores del pipeline
```

No toda esta información debe mostrarse al usuario.

Debe existir para:

- Depuración.
- Evaluación.
- Auditoría.
- Mejora de calidad.
- Detección de errores.
- Comparación entre modelos.

---

## 9. Arquitectura del retrieval

El retrieval actual funciona así:

```text
Pregunta
↓
Embedding de la pregunta
↓
Semantic search
↓
Keyword search
↓
Fusión de resultados
↓
Reranking
↓
Top K chunks
```

### Semantic search

Busca similitud por significado.

Ejemplo:

```text
"correo de Kelly"
```

puede encontrar:

```text
"correo electrónico"
"email"
"dirección de contacto"
```

aunque las palabras no sean idénticas.

### Keyword search

Busca coincidencias literales.

Es especialmente útil para:

- Nombres.
- Correos.
- Cédulas.
- Teléfonos.
- Fechas.
- Códigos.
- Números de contrato.
- Referencias exactas.

### Hybrid retrieval

Combina búsqueda semántica y búsqueda textual.

Esto evita depender completamente de una sola estrategia.

### Reranking

El reranker toma candidatos y calcula cuál evidencia responde mejor la pregunta.

Flujo:

```text
Top 20 candidatos
↓
Reranker
↓
Top 5 finales
```

---

## 10. Arquitectura del scoring

Cada chunk puede tener:

```text
distance
score
```

### Distance

Es la distancia semántica original obtenida desde pgvector.

Una distancia menor normalmente indica mayor similitud.

### Score

Es el valor final después de aplicar el reranker.

Puede considerar:

```text
Distancia semántica
Coincidencias de palabras
Entidades
Patrones
Intención
Metadata
Tipo de documento
Recencia
Autoridad de la fuente
```

Ejemplo conceptual:

```text
score final =
distance semántica
- keyword boost
- entity boost
- pattern boost
- metadata boost
```

El score permite explicar por qué un chunk quedó por encima de otro.

---

## 11. Query analysis futuro

El sistema no debe depender de reglas rígidas como:

```python
if "correo" in query:
```

La arquitectura futura debe incluir:

```text
Query Analyzer
```

Responsabilidades:

```text
Detectar intención
Detectar entidades
Detectar tipo de dato solicitado
Normalizar la consulta
Detectar restricciones
Detectar contexto
```

Ejemplo:

Pregunta:

```text
¿Cuál es el correo de Kelly?
```

Resultado esperado:

```text
Entidad:
Kelly

Intención:
extraer dato

Tipo de dato:
correo electrónico
```

---

## 12. Query expansion futuro

La consulta debe poder expandirse.

Ejemplo:

```text
correo
```

puede expandirse a:

```text
correo
email
e-mail
mail
correo electrónico
dirección electrónica
```

Otro ejemplo:

```text
fecha de nacimiento
```

puede expandirse a:

```text
nacimiento
fecha de nacimiento
birthday
nació
lugar y fecha de nacimiento
```

Esto mejora la recuperación sin llenar el código de condiciones específicas.

---

## 13. Roadmap arquitectónico

## Fase actual: motor RAG local

```text
Ingesta PDF               ✅
Extracción de texto       ✅
Chunking                  ✅
Embeddings locales        ✅
pgvector                  ✅
Búsqueda semántica        ✅
Búsqueda por keywords     ✅
Búsqueda híbrida          ✅
Reranking                 ✅
LLM local                 ✅
Fuentes auditables        ✅
```

---

## Siguiente fase: calidad del retrieval

```text
Score explicable
Query analyzer
Query expansion
Entity detection
Intent detection
Filtros por documento
Filtros por metadata
Umbral mínimo de relevancia
Normalización de texto
Mejor chunking
```

---

## Fase posterior: operación profesional

```text
Background jobs
Procesamiento asíncrono
Estados de documento
Reintentos
Manejo de errores
Logging estructurado
Métricas
Tests unitarios
Tests de integración
Evaluación automática de RAG
```

---

## Fase de producto

```text
Conversaciones
Historial
Colecciones
Workspaces
Compartir documentos
Frontend
Dashboard administrativo
Filtros
Roles avanzados
API pública
```

---

## Fase multimodal

```text
DOCX
TXT
Excel
Imágenes
OCR
Audio
Video
Correos
Bases de datos
APIs
Sensores
```

---

## 14. Principios de desarrollo

OmniCortex seguirá estas reglas:

```text
1. Los routers no contienen lógica compleja.
2. Cada servicio tiene una responsabilidad.
3. Los proveedores de IA deben ser reemplazables.
4. Toda respuesta debe poder mostrar evidencia.
5. La seguridad se aplica desde la recuperación.
6. Los cambios de esquema se realizan con Alembic.
7. El pipeline debe ser observable.
8. Primero se valida cada componente aislado.
9. Después se integra.
10. No se agrega complejidad sin una necesidad real.
11. El código explica qué hace.
12. La documentación explica por qué existe.
13. Los errores de IA deben poder rastrearse por etapa.
14. Las fuentes deben pertenecer al usuario autenticado.
15. El sistema debe poder cambiar de modelo sin reescribir el pipeline.
```

---

## 15. Stack tecnológico actual

```text
Python
FastAPI
PostgreSQL
SQLAlchemy
Alembic
Docker
pgvector
PyMuPDF
Ollama
nomic-embed-text
qwen2.5:3b
JWT
RBAC
DBeaver
```

---

## 16. Estado actual de OmniCortex

OmniCortex ya puede:

```text
Registrar usuarios
Autenticar usuarios
Autorizar por roles
Subir documentos PDF
Guardar archivos
Extraer texto
Dividir texto en chunks
Generar embeddings locales
Guardar vectores en PostgreSQL
Buscar por similitud semántica
Combinar semantic search y keyword search
Reordenar resultados
Construir prompts
Responder con un LLM local
Mostrar las fuentes utilizadas
Aislar documentos por usuario
```

El sistema ya no es solamente un CRUD.

Es una primera versión funcional de un:

```text
Knowledge Retrieval Engine
```

o:

```text
Motor de conocimiento con RAG local
