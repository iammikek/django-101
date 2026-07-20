# Getting Fast at Django

A step-by-step **Django + DRF** port of [fastAPI-101](https://github.com/iammikek/fastAPI-101) — same items/categories API, same Laravel crossover style, different framework.

**Monolith:** Django owns models, database, admin, JSON API, and a **server-rendered shop** at `/shop/` (not a frontend calling FastAPI or its own JSON API).

---

## What's Included

1. **Django project** (`config/`) with settings, URLs, health routes
2. **`accounts` app** — email-based `User`, register/login/me, JWT (SimpleJWT)
3. **`catalog` app** — `Category` + `Item` models, DRF ViewSets, service layer
4. **Django Admin** — manage items and categories in `/admin`
5. **Service layer** — `catalog/services.py` (mirrors fastAPI-101 business logic)
6. **Pagination** — `{ items, total, skip, limit }` (same shape as FastAPI Step 20)
7. **Filtering** — `min_price`, `max_price`, `category_id`, `name_contains` on `GET /items`
8. **Item stats** — `GET /items/stats/summary` with per-category breakdown
9. **JWT auth** — Bearer tokens on write endpoints (register/login/me)
10. **Rate limiting** — 10/min auth, 60/min writes (DRF throttling)
11. **PostgreSQL in Docker** — port **8001** (so fastAPI-101 can keep **8000**)
12. **Catalog Shop** — server-rendered HTML at `/shop/` (templates, forms, session auth) — see **[docs/frontend.md](docs/frontend.md)**
13. **OpenAPI docs** — Swagger UI at `/docs` (drf-spectacular) — see **[docs/api-docs.md](docs/api-docs.md)**
14. **Tests** — pytest-django (37 tests)
15. **CI** — GitHub Actions (ruff + pytest)

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Project Structure](#2-project-structure)
3. [FastAPI ↔ Django map](#3-fastapi--django-map)
4. [Step 1: Project setup](#4-step-1-project-setup)
5. [Step 2: Item model + migrations](#5-step-2-item-model--migrations)
6. [Step 3: Django Admin](#6-step-3-django-admin)
7. [Step 4: DRF serializers](#7-step-4-drf-serializers)
8. [Step 5: Item ViewSet (CRUD)](#8-step-5-item-viewset-crud)
9. [Step 6: Tests](#9-step-6-tests)
10. [Step 7: Categories + FK](#10-step-7-categories--fk)
11. [Step 8: Filtering](#11-step-8-filtering)
12. [Step 9: Pagination metadata](#12-step-9-pagination-metadata)
13. [Step 10: Item stats capstone](#13-step-10-item-stats-capstone)
14. [Step 11: JWT authentication](#14-step-11-jwt-authentication)
15. [Step 12: Rate limiting](#15-step-12-rate-limiting)
16. [Step 13: PostgreSQL (Docker)](#16-step-13-postgresql-docker)
17. [Step 14: Service layer tests](#17-step-14-service-layer-tests)
18. [Step 15: Server-rendered frontend](#18-step-15-server-rendered-frontend)
19. [Step 16: OpenAPI docs (Swagger UI)](#19-step-16-openapi-docs-swagger-ui)
20. [Quick Reference](#20-quick-reference)

---

## 1. Quick Start

### Local Python (SQLite)

```bash
cd django-101
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py runserver 8001
```

Open **http://127.0.0.1:8001/** — root message  
**http://127.0.0.1:8001/items** — item list JSON (empty)  
**http://127.0.0.1:8001/docs** — interactive API docs (Swagger UI)  
**http://127.0.0.1:8001/shop/** — browser UI (register, browse, add items)

### Docker (PostgreSQL)

```bash
docker compose up --build
```

API on **http://localhost:8001** (fastAPI-101 uses 8000).

### Tests

```bash
pytest tests/ -v
```

---

## 2. Project Structure

```
django-101/
├── manage.py
├── config/                 # Project settings (Laravel config/)
│   ├── settings.py
│   ├── urls.py
│   ├── views.py            # GET /, GET /health
│   └── exceptions.py       # { detail, code } error handler
├── accounts/               # User + auth
│   ├── models.py           # Custom User (email login)
│   ├── views.py            # register, login, me
│   └── admin.py
├── catalog/                # Items + categories
│   ├── models.py
│   ├── serializers.py
│   ├── services.py         # Business logic (shared by API + shop)
│   ├── views.py            # DRF ViewSets (JSON API)
│   ├── web_views.py        # Template views (/shop/)
│   ├── forms.py            # HTML forms
│   ├── urls_web.py         # /shop/ routes
│   ├── templates/catalog/  # Shop pages
│   ├── static/catalog/     # Shop CSS
│   ├── admin.py
│   ├── exceptions.py
│   └── throttles.py
├── templates/
│   └── base.html           # Shop layout
├── docs/
│   ├── frontend.md         # How the browser UI was built
│   └── api-docs.md         # Swagger UI at /docs
├── tests/
├── requirements.txt
├── docker-compose.yml
└── README.md
```

---

## 3. FastAPI ↔ Django map

| fastAPI-101 | django-101 |
|-------------|------------|
| `app/main.py` | `config/urls.py` + `config/settings.py` |
| `APIRouter` | DRF `ViewSet` + `DefaultRouter` |
| Pydantic schemas | DRF `Serializer` |
| SQLAlchemy models | Django ORM `models.Model` |
| Alembic | `makemigrations` / `migrate` |
| `Depends(get_current_user)` | `permission_classes = [IsAuthenticated]` |
| `python-jose` JWT | `rest_framework_simplejwt` |
| `slowapi` | DRF `throttle_classes` |
| pytest + TestClient | pytest-django + `APIClient` |
| `/docs` (Swagger) | `/docs` (drf-spectacular) |
| — | **Django Admin** `/admin` |

| Laravel | django-101 |
|---------|------------|
| `artisan migrate` | `python manage.py migrate` |
| Eloquent | Django ORM |
| API Resources | DRF Serializers |
| `auth:sanctum` | JWT + `IsAuthenticated` |
| `throttle:10,1` | `AuthRateThrottle` / `WriteRateThrottle` |
| Filament/Nova | Django Admin (built-in) |

---

## 4. Step 1: Project setup

```bash
django-admin startproject config .
python manage.py startapp catalog
python manage.py startapp accounts
```

Add to `INSTALLED_APPS`: `rest_framework`, `accounts`, `catalog`, `corsheaders`.

**Laravel parallel:** `laravel new` + registering providers.

---

## 5. Step 2: Item model + migrations

**`catalog/models.py`:**

```python
class Item(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
```

```bash
python manage.py makemigrations
python manage.py migrate
```

**Laravel parallel:** `php artisan make:model Item -m`

---

## 6. Step 3: Django Admin

**`catalog/admin.py`** — register `Item` and `Category`.

```bash
python manage.py createsuperuser   # use email as login
```

Open **http://127.0.0.1:8001/admin/** — create items without writing API clients.

**This is the big Django win** — no equivalent in fastAPI-101.

---

## 7. Step 4: DRF serializers

**`catalog/serializers.py`** — `ItemSerializer`, `ItemCreateSerializer`, `ItemUpdateSerializer`.

| Pydantic (FastAPI) | DRF Serializer |
|--------------------|----------------|
| `Field(gt=0)` | `DecimalField(min_value=0.01)` |
| `from_attributes=True` | `ModelSerializer` |
| partial update | `partial=True` on serializer |

---

## 8. Step 5: Item ViewSet (CRUD)

**`catalog/views.py`** + **`config/urls.py`:**

```python
router = DefaultRouter(trailing_slash=False)
router.register("items", ItemViewSet, basename="item")
```

| Method | Path | Auth |
|--------|------|------|
| GET | `/items` | Public |
| GET | `/items/{id}` | Public |
| POST | `/items` | JWT |
| PATCH | `/items/{id}` | JWT |
| DELETE | `/items/{id}` | JWT |

**Laravel parallel:** `Route::apiResource('items', ItemController::class)`

---

## 9. Step 6: Tests

**`tests/conftest.py`** — `APIClient`, `authed_client`, factories.

```bash
pytest tests/ -v
```

**34 tests** covering auth, items, categories, services, health, and shop pages.

---

## 10. Step 7: Categories + FK

**`Category` model** + `Item.category` ForeignKey (nullable).

Business rules in **`catalog/services.py`**:
- Duplicate category name → **409** `CATEGORY_NAME_EXISTS`
- Delete category with items → **409** `CATEGORY_IN_USE`
- Invalid `category_id` on item → **404** `CATEGORY_NOT_FOUND`

---

## 11. Step 8: Filtering

`GET /items?min_price=10&category_id=1&name_contains=widget`

Implemented in `ItemService._items_queryset()` with `filter(price__gte=...)`, `name__icontains`.

**Laravel parallel:** query scopes / `when()` filters.

---

## 12. Step 9: Pagination metadata

Same response shape as fastAPI-101:

```json
{
  "items": [ ... ],
  "total": 42,
  "skip": 0,
  "limit": 10
}
```

Query params: `skip` (≥0), `limit` (1–100). Invalid values → **422**.

---

## 13. Step 10: Item stats capstone

`GET /items/stats/summary` — ViewSet `@action`:

```json
{
  "total_items": 5,
  "average_price": 12.5,
  "min_price": 5.0,
  "max_price": 20.0,
  "uncategorized_count": 1,
  "by_category": [
    { "category_id": 1, "category_name": "Tools", "item_count": 2, "average_price": 10.0 }
  ]
}
```

Logic in `ItemService.get_stats()` — mirrors fastAPI-101 SQL aggregates.

---

## 14. Step 11: JWT authentication

| Endpoint | Purpose |
|----------|---------|
| `POST /auth/register` | `{ email, password }` → 201 |
| `POST /auth/login` | `{ username, password }` — **username = email** (FastAPI parity) |
| `GET /auth/me` | Bearer token required |

Write endpoints on `/items` and `/categories` require `Authorization: Bearer <token>`.

**Libraries:** `djangorestframework-simplejwt`

**Try it:**

```bash
# Register
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"password123"}'

# Login
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"you@example.com","password":"password123"}'

# Create item
curl -X POST http://localhost:8001/items \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Widget","price":"9.99"}'
```

---

## 15. Step 12: Rate limiting

| Endpoint group | Limit |
|----------------|-------|
| `/auth/register`, `/auth/login` | 10/minute per IP |
| POST/PATCH/DELETE on items & categories | 60/minute per IP |

**429 response:** `{ "detail": "Rate limit exceeded", "code": "RATE_LIMIT_EXCEEDED" }`

**Laravel parallel:** `throttle:10,1` middleware.

---

## 16. Step 13: PostgreSQL (Docker)

```bash
docker compose up --build
```

- **`db`** — Postgres 16 on host port **5433**
- **`api`** — Django on host port **8001**
- Migrations run on startup

Verify:

```bash
docker compose exec db psql -U django -d django101 -c "\dt"
```

Local `runserver` still uses SQLite (`db.sqlite3`).

---

## 17. Step 14: Service layer tests

**`tests/test_services.py`** — unit tests for `CategoryService` and `ItemService` without HTTP.

**Laravel parallel:** testing service classes / actions directly.

---

## 18. Step 15: Server-rendered frontend

A **Catalog Shop** at `/shop/` demonstrates full-stack Django alongside the JSON API:

| Shop (browser) | API (JSON) |
|----------------|------------|
| `/shop/register/` — signup + auto-login | `POST /auth/register` — JSON only |
| `/shop/login/` — session cookie | `POST /auth/login` — JWT |
| `/shop/items/` — HTML table + filters | `GET /items` — JSON list |
| `/shop/items/new/` — HTML form | `POST /items` — Bearer token |

The shop calls **`catalog/services.py` directly** — it does not fetch `/items`. Same monolith pattern as Laravel web routes using Eloquent, not internal HTTP.

**Full walkthrough:** **[docs/frontend.md](docs/frontend.md)** — architecture, file layout, auth split, request flow, tests, and why we did not wire the UI to the API.

```bash
python manage.py runserver 8001
# http://127.0.0.1:8001/shop/register/
```

---

## 19. Step 16: OpenAPI docs (Swagger UI)

Interactive API browser — same idea as fastAPI-101’s **http://localhost:8000/docs**.

**Library:** `drf-spectacular`

| URL | Purpose |
|-----|---------|
| `/docs` | Swagger UI — try all endpoints |
| `/openapi.json` | Raw OpenAPI 3 schema |

**Try it:**

1. Open **http://127.0.0.1:8001/docs**
2. **POST /auth/register** → create a user
3. **POST /auth/login** → copy `access_token`
4. Click **Authorize** → `Bearer <token>`
5. Try **POST /items** or **POST /categories**

**Full walkthrough:** **[docs/api-docs.md](docs/api-docs.md)** — wiring, JWT flow, comparison with browsable API and fastAPI-101.

---

## 20. Quick Reference

| Goal | Command |
|------|---------|
| Activate venv | `source .venv/bin/activate` |
| Migrate | `python manage.py migrate` |
| Run local (SQLite) | `python manage.py runserver 8001` |
| Open shop UI | http://127.0.0.1:8001/shop/ |
| Open API docs | http://127.0.0.1:8001/docs |
| Frontend docs | [docs/frontend.md](docs/frontend.md) |
| API docs guide | [docs/api-docs.md](docs/api-docs.md) |
| Create admin user | `python manage.py createsuperuser` |
| Run tests | `pytest tests/ -v --cov` |
| Docker + Postgres | `docker compose up --build` |
| Stop Docker | `docker compose down` |
| Django shell | `python manage.py shell` |

---

## Compare with fastAPI-101

Run both side by side:

| | fastAPI-101 | django-101 |
|--|-------------|------------|
| Port (local/Docker) | 8000 | 8001 |
| Root message | `Hello from FastAPI!` | `Hello from Django!` |
| API shape | Same endpoints | Same endpoints |
| Admin UI | No | `/admin` |
| Browser shop | No | `/shop/` |
| OpenAPI docs | `/docs` | `/docs` |

You now have the **same API** implemented twice — once FastAPI (async-capable, explicit), once Django (monolith, batteries-included). That is the crossover.

---

## *-101 Family

### API backends

| Repo | Port | Type | Stack |
|------|------|------|-------|
| [fastAPI-101](https://github.com/iammikek/fastAPI-101) | 8000 | API-only | FastAPI, SQLAlchemy |
| [**django-101**](https://github.com/iammikek/django-101) | **8001** | Monolith | Django + DRF + shop |
| [symfony-101](https://github.com/iammikek/symfony-101) | 8002 | Monolith | Symfony + shop |
| [laravel-101](https://github.com/iammikek/laravel-101) | 8003 | Monolith | Laravel + shop |
| [framework-x-101](https://github.com/iammikek/framework-x-101) | 8004 | Monolith | Framework X + shop |
| [orchestr-101](https://github.com/iammikek/orchestr-101) | 8005 | Monolith | Orchestr + shop |
| [nest-101](https://github.com/iammikek/nest-101) | 8006 | API-only | NestJS, TypeScript |
| [express-101](https://github.com/iammikek/express-101) | 8007 | API-only | Express, Vitest |
| [go-101](https://github.com/iammikek/go-101) | 8000* | API-only | Gin, GORM |
| [fortran-101](https://github.com/iammikek/fortran-101) | 8008 | API-only | Fortran, fpm |
| [java-101](https://github.com/iammikek/java-101) | 8009 | API-only | Spring Boot, JPA, Flyway |
| [dotNet-101](https://github.com/iammikek/dotNet-101) | 8010 | API-only | ASP.NET Core, xUnit |
| [flask-101](https://github.com/iammikek/flask-101) | 8011 | API-only | Flask, pytest |
| [rails-101](https://github.com/iammikek/rails-101) | 8012 | Monolith | Rails + shop |
| [geblang-101](https://github.com/iammikek/geblang-101) | 8013 | API-only | Geblang, SQLite |
\* go-101 also uses port 8000 — run one backend at a time, or change port in config.

### Other clients

| Repo | Platform | Stack |
|------|----------|-------|
| [flutter-101](https://github.com/iammikek/flutter-101) | Mobile / desktop | Flutter (iOS, macOS, Android) |
| [react-101](https://github.com/iammikek/react-101) | Web browser | React 19, Vite, Vitest |
| [vue-101](https://github.com/iammikek/vue-101) | Web browser | Vue 3, Vite, Pinia |
| [alpine-101](https://github.com/iammikek/alpine-101) | Web browser | Alpine.js, Vite, Vitest |

### Suggested pairing

- **Compare Python stacks:** [fastAPI-101](https://github.com/iammikek/fastAPI-101) (8000) vs django-101 (8001) vs [flask-101](https://github.com/iammikek/flask-101) (8011)
- **Monolith shop vs SPA:** django-101 `/shop/` vs [react-101](https://github.com/iammikek/react-101), [vue-101](https://github.com/iammikek/vue-101), or [alpine-101](https://github.com/iammikek/alpine-101)

Catalogue: [automica.io/learning-101](https://automica.io/learning-101.html)
