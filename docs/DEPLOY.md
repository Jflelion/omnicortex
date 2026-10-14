# Despliegue de la demo pública

La demo usa servicios hospedados en lugar de Ollama, para no necesitar GPU:

| Pieza | Servicio | Costo |
|---|---|---|
| API (FastAPI, Docker) | Render, plan Free | 0 USD |
| Frontend (React) | Render, Static Site | 0 USD |
| PostgreSQL + pgvector | Neon, plan Free | 0 USD |
| LLM | Claude Haiku 5.5 (`claude-haiku-5-5`) | ~0,0003 USD por pregunta |
| Embeddings | Nomic API, `nomic-embed-text-v1.5` (768 dims) | tier gratuito |

El cambio de proveedor es solo configuración (`LLM_PROVIDER=anthropic`, `EMBEDDING_PROVIDER=nomic`); en local se sigue usando Ollama. Ver ADR-012 en [ENGINEERING_DECISIONS.md](ENGINEERING_DECISIONS.md).

## 1. Base de datos en Neon

1. Crea un proyecto en <https://neon.tech> (región cercana a la de Render, p. ej. `US East`).
2. Copia la *connection string* (la directa, no la *pooled*). Tiene la forma
   `postgresql://usuario:clave@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require`.

No hace falta crear tablas ni la extensión `vector`: la API aplica las migraciones al arrancar.

## 2. Claves de API

- **Anthropic**: crea una clave en <https://console.anthropic.com>. En *Limits*, fija un límite de gasto mensual bajo (por ejemplo 5 USD): el registro en la demo es público.
- **Nomic**: crea una clave en <https://atlas.nomic.ai>.

## 3. Render (Blueprint)

1. En <https://dashboard.render.com>: **New → Blueprint** y elige el repositorio. Render lee [`render.yaml`](../render.yaml) y crea dos servicios: `omnicortex-api` y `omnicortex`.
2. Te pedirá los valores marcados como secretos:
   - `DATABASE_URL`: la de Neon.
   - `ANTHROPIC_API_KEY` y `NOMIC_API_KEY`.

   `SECRET_KEY` se genera solo.
3. Cuando termine, comprueba las URLs asignadas. Si Render añadió un sufijo a algún nombre (porque ya existía), actualiza en `render.yaml`:
   - `CORS_ORIGINS` de la API → URL del frontend.
   - `VITE_API_URL` del frontend → URL de la API.

   Haz commit y push; Render redespliega.

## 4. Verificación

- `https://omnicortex-api.onrender.com/health` debe responder `"status": "ok"` con `database`, `anthropic` y `nomic`.
- Abre `https://omnicortex.onrender.com`, crea una cuenta, sube un PDF y espera a que pase a **Listo**.

## Limitaciones del plan gratuito

- La API se duerme tras 15 minutos sin tráfico; la primera petición tarda hasta un minuto. El login muestra un aviso mientras tanto.
- El disco de Render es efímero: los PDF subidos se pierden al reiniciar. No afecta a la demo, porque el texto, los chunks y los embeddings se guardan en Neon al subir el archivo.
- El JWT dura 120 minutos en la demo (`ACCESS_TOKEN_EXPIRE_MINUTES`).
