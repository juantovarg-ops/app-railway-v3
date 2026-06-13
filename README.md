# Smart Product Search

Búsqueda semántica de productos sin dependencias externas complicadas.

## Stack

| Servicio | Rol |
|----------|-----|
| **PostgreSQL + pgvector** | Embeddings vectoriales + logs de búsqueda |
| **MongoDB** | Catálogo de productos (documentos flexibles) |
| **Redis** | Cache de embeddings (TTL 24 h) |
| **Gemini AI** | `text-embedding-004` (768d) + `gemini-2.0-flash` |

## Flujo

```
query → Redis cache? → [miss] Gemini embed → pgvector cosine search
                     → [hit]  ────────────────────^
                                     ↓
                               MongoDB fetch docs
                                     ↓
                            Gemini genera resumen
                                     ↓
                            PostgreSQL log búsqueda
```

## Setup local

```bash
cp .env.example .env
# Agrega tu GEMINI_API_KEY

docker compose up --build
# → http://localhost:8501
# Sidebar → "Seed productos demo" → busca algo
```

## Deploy Railway

### 1. Servicios de infraestructura

Desde **+ New → Database** agrega:
- **PostgreSQL** → Railway ya incluye pgvector en su imagen
- **MongoDB**
- **Redis**

### 2. Deploy de la app

Conecta tu repositorio GitHub o usa `railway up` desde la CLI.

### 3. Variables de entorno

Railway inyecta `DATABASE_URL`, `MONGO_URL`, y `REDIS_URL` automáticamente
si los servicios están en el mismo proyecto. Solo debes agregar manualmente:

```
MONGO_DB=smartsearch
GEMINI_API_KEY=<tu clave>
```
