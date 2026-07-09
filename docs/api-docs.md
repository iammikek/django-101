# OpenAPI docs (Swagger UI)

django-101 exposes interactive API documentation via **[drf-spectacular](https://drf-spectacular.readthedocs.io/)** — the Django equivalent of FastAPI’s `/docs`.

---

## URLs

| URL | Purpose |
|-----|---------|
| **http://127.0.0.1:8001/docs** | Swagger UI — browse and try every endpoint |
| **http://127.0.0.1:8001/openapi.json** | Raw OpenAPI 3 schema (JSON) |

Same port as the API (**8001**). fastAPI-101 serves its docs at **http://localhost:8000/docs**.

---

## Quick start

```bash
cd django-101
source .venv/bin/activate
python manage.py runserver 8001
```

Open **http://127.0.0.1:8001/docs** in your browser.

You’ll see all endpoints grouped by resource:

- `items` — list, create, retrieve, update, delete, stats
- `categories` — full CRUD
- `auth` — register, login, me
- `health` — if included in schema from views

---

## Try authenticated writes (JWT)

Write endpoints require a Bearer token. Workflow matches FastAPI `/docs`:

### 1. Register

In Swagger UI, open **POST /auth/register** → **Try it out**:

```json
{
  "email": "you@example.com",
  "password": "password123"
}
```

Execute → **201** with `{ "id", "email" }`.

### 2. Login

Open **POST /auth/login** → **Try it out**:

```json
{
  "username": "you@example.com",
  "password": "password123"
}
```

Execute → copy `access_token` from the response.

> The login field is named `username` for fastAPI-101 parity — it holds your **email**.

### 3. Authorize

Click the **Authorize** button (top right) → enter:

```
Bearer <paste access_token here>
```

Or just the raw token if Swagger adds `Bearer` automatically (depends on UI version).

### 4. Call write endpoints

Try **POST /items**, **POST /categories**, **PATCH /items/{id}**, etc. Swagger sends the `Authorization` header for you.

### 5. Current user

**GET /auth/me** — returns the logged-in user when authorized.

---

## How it’s wired

### Package

`drf-spectacular` in `requirements.txt`.

### Settings (`config/settings.py`)

```python
INSTALLED_APPS = [
    ...
    "drf_spectacular",
]

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    ...
}

SPECTACULAR_SETTINGS = {
    "TITLE": "django-101 API",
    "DESCRIPTION": "...",
    "VERSION": "1.0.0",
}
```

### URLs (`config/urls.py`)

```python
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("openapi.json", SpectacularAPIView.as_view(), name="schema"),
    path("docs", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    ...
]
```

### Schema hints

- **ViewSets** (`ItemViewSet`, `CategoryViewSet`) — auto-generated from DRF serializers and `@action` methods.
- **Auth views** — `@extend_schema` on `RegisterView`, `LoginView`, `MeView` in `accounts/views.py` for clear request/response shapes.

---

## Compare interfaces

django-101 now has **four** ways to interact with the backend:

| Interface | URL | Best for |
|-----------|-----|----------|
| **Swagger UI** | `/docs` | Exploring and trying the full API |
| **JSON API** | `/items`, `/auth/...` | curl, mobile, SPA |
| **Catalog Shop** | `/shop/` | Server-rendered browser UI |
| **Django Admin** | `/admin/` | Staff CRUD on models |

```
/docs  ──► OpenAPI schema ◄── same endpoints as /items, /categories, /auth/*
                │
                ▼
         catalog/services.py ──► database
```

The shop and admin do **not** use `/docs` — they call services or models directly.

---

## DRF browsable API vs Swagger

| | `/docs` (Swagger) | `/items` in browser (browsable API) |
|--|-------------------|-------------------------------------|
| All endpoints in one UI | Yes | One endpoint per page |
| JWT Authorize button | Yes | No |
| FastAPI-like experience | Yes | Partial |

Prefer **`/docs`** for exploring the full API.

---

## Tests

```bash
pytest tests/test_docs.py -v
```

Checks that `/openapi.json` lists key paths and `/docs` returns the Swagger page.

---

## Production note

Schema and Swagger UI are enabled for local learning (`DEBUG=True`). In production you typically:

- Disable or restrict `/docs` and `/openapi.json` behind auth or `DEBUG` checks
- Generate a static schema in CI if needed for client SDKs

Not configured in this tutorial project — fine for local dev.

---

## fastAPI-101 side-by-side

| | fastAPI-101 | django-101 |
|--|-------------|------------|
| Docs UI | http://localhost:8000/docs | http://127.0.0.1:8001/docs |
| OpenAPI JSON | http://localhost:8000/openapi.json | http://127.0.0.1:8001/openapi.json |
| Generator | Built into FastAPI | drf-spectacular add-on |

Same workflow: register → login → Authorize → try writes.
