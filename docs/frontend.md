# Server-rendered frontend (Catalog Shop)

This document explains how the **browser UI** at `/shop/` was built — a classic Django full-stack frontend that sits alongside the JSON API, not a JavaScript client calling `/items`.

---

## Why two interfaces?

django-101 is primarily an **API learning project** (DRF, JWT, same shape as fastAPI-101). The shop was added to show what **full-stack Django** looks like compared to API-only:

| | JSON API | Catalog Shop (`/shop/`) |
|--|----------|-------------------------|
| **Response** | `application/json` | `text/html` |
| **Auth** | JWT Bearer token | Session cookie |
| **Views** | DRF ViewSets (`catalog/views.py`) | Django class-based views (`catalog/web_views.py`) |
| **Validation** | DRF serializers | Django forms (`catalog/forms.py`) |
| **Client** | curl, mobile, future SPA | Browser (full page loads) |

Both paths use the **same models and service layer** — the shop does **not** HTTP-call `/items`. That is intentional: in a Django monolith, HTML views talk to `ItemService` directly (like a Laravel controller using Eloquent, not `Http::get('/api/items')`).

See [Should the frontend call the API?](#should-the-frontend-call-the-api) at the end.

---

## Architecture

```
Browser request
      │
      ▼
/shop/*  ──► catalog/web_views.py  ──► catalog/forms.py (POST/GET validation)
      │              │
      │              ▼
      │        catalog/services.py  ──► catalog/models.py  ──► SQLite / Postgres
      │
      └──► templates/*.html + static/catalog/style.css
             (server builds HTML, sends to browser)


Separate path:

/items  ──► catalog/views.py (DRF) ──► same services.py ──► same DB
```

**Laravel parallel:** `/shop/*` ≈ web routes + Blade + `FormRequest`; `/items` ≈ API routes + API Resources.

---

## URLs

Mounted in `config/urls.py`:

```python
path("shop/", include("catalog.urls_web")),
```

| URL | View | Auth | Purpose |
|-----|------|------|---------|
| `/shop/` | `ShopHomeView` | Public | Landing page + catalog stats |
| `/shop/items/` | `ItemListView` | Public | Browse/filter items (paginated) |
| `/shop/items/<id>/` | `ItemDetailView` | Public | Single item page |
| `/shop/items/new/` | `ItemCreateView` | Session login | Add item via HTML form |
| `/shop/register/` | `ShopRegisterView` | Public | Create account + auto-login |
| `/shop/login/` | `ShopLoginView` | Public | Session login |
| `/shop/logout/` | `ShopLogoutView` | POST | End session |

Route names (for `{% url %}`): `shop-home`, `shop-item-list`, `shop-item-detail`, `shop-item-create`, `shop-register`, `shop-login`, `shop-logout`.

---

## File layout

```
django-101/
├── templates/
│   └── base.html                 # Site layout (nav, messages, footer)
├── catalog/
│   ├── urls_web.py               # /shop/ URLconf
│   ├── web_views.py              # Template views (not DRF)
│   ├── forms.py                  # HTML forms
│   ├── static/catalog/
│   │   └── style.css             # Shop styles
│   └── templates/catalog/
│       ├── home.html
│       ├── item_list.html
│       ├── item_detail.html
│       ├── item_form.html
│       ├── login.html
│       └── register.html
└── config/
    └── settings.py               # TEMPLATES DIRS, LOGIN_URL, LOGIN_REDIRECT_URL
```

---

## How each layer works

### 1. Templates

Django’s template language builds HTML on the server.

- **`templates/base.html`** — shared layout: header nav, flash messages, footer, CSS link.
- **App templates** — extend base with `{% extends "base.html" %}` and fill `{% block content %}`.
- **Context** — views pass data (e.g. `stats`, `items`, `form`) into templates.

Example from the item list — loop over queryset in HTML:

```django
{% for item in items %}
  <tr>
    <td><a href="{% url 'shop-item-detail' item.pk %}">{{ item.name }}</a></td>
    <td>${{ item.price }}</td>
  </tr>
{% endfor %}
```

**Settings:** `TEMPLATES["DIRS"]` includes the project `templates/` folder; `APP_DIRS: True` finds `catalog/templates/`.

### 2. Views (`catalog/web_views.py`)

Class-based views map URLs to template + logic:

| View | Base class | Role |
|------|------------|------|
| `ShopHomeView` | `TemplateView` | Renders home; calls `ItemService.get_stats()` |
| `ItemListView` | `ListView` | Paginated list; filters via `ItemFilterForm` + `ItemService.list_items()` |
| `ItemDetailView` | `DetailView` | Single `Item` by pk |
| `ItemCreateView` | `CreateView` + `LoginRequiredMixin` | POST form → `ItemService.create()` |
| `ShopRegisterView` | `FormView` | POST form → create user → `login()` → redirect |
| `ShopLoginView` | `LoginView` | Session auth |
| `ShopLogoutView` | `LogoutView` | Clears session (POST only) |

**Item create** reuses the service layer instead of `form.save()` on the model directly:

```python
item = ItemService.create(
    name=form.cleaned_data["name"],
    price=Decimal(str(form.cleaned_data["price"])),
    description=form.cleaned_data.get("description"),
    category_id=category.pk if category else None,
)
```

Same business rules as `POST /items` (category validation, etc.).

### 3. Forms (`catalog/forms.py`)

| Form | Used for |
|------|----------|
| `UserRegistrationForm` | `/shop/register/` — email + password (extends `UserCreationForm`) |
| `EmailAuthenticationForm` | `/shop/login/` — email labelled correctly for custom User model |
| `ItemFilterForm` | GET filters on item list (`name_contains`, category, min/max price) |
| `ItemForm` | Create item — `ModelForm` for name, description, price, category |

Forms handle validation and HTML field rendering (`{{ form.as_p }}`). POST forms include **CSRF** via `{% csrf_token %}`.

### 4. Auth — session vs JWT

The shop and API use **different auth mechanisms** for the same `User` model:

| Action | Shop (browser) | API |
|--------|----------------|-----|
| Register | `POST /shop/register/` → session cookie | `POST /auth/register` → JSON only |
| Login | `POST /shop/login/` → session cookie | `POST /auth/login` → JWT |
| Protected write | `@login_required` / `LoginRequiredMixin` | `Authorization: Bearer …` |

**Register on the shop auto-logs you in** (`login(request, user)` after `form.save()`). API register does not — clients must call `/auth/login` for a token.

**Settings:**

```python
LOGIN_URL = "/shop/login/"
LOGIN_REDIRECT_URL = "/shop/"
```

### 5. Static files

`catalog/static/catalog/style.css` — loaded with `{% load static %}` and `{% static 'catalog/style.css' %}`. No JS framework; plain CSS for layout, tables, forms, messages.

In development, `runserver` serves static files automatically when `django.contrib.staticfiles` is installed.

### 6. Messages

Flash feedback uses Django’s messages framework (`messages.success`, `messages.info`) and renders in `base.html` — e.g. “Account created. You are logged in.”

---

## Request walkthrough: add an item

1. User visits `/shop/items/new/` — must be logged in (else redirect to `/shop/login/?next=…`).
2. Browser GET → `ItemCreateView` → renders `item_form.html` with empty `ItemForm`.
3. User submits POST with name, price, category, CSRF token.
4. `ItemForm` validates input.
5. `form_valid()` calls `ItemService.create(...)`.
6. Redirect to `/shop/items/<id>/` with success message.

Compare to API flow: same service call, but API uses JSON body + JWT instead of form + session.

---

## Try it

With the server running on port **8001**:

```bash
python manage.py runserver 8001
```

| Page | URL |
|------|-----|
| Shop home | http://127.0.0.1:8001/shop/ |
| Browse items | http://127.0.0.1:8001/shop/items/ |
| Register | http://127.0.0.1:8001/shop/register/ |
| Log in | http://127.0.0.1:8001/shop/login/ |
| JSON API (contrast) | http://127.0.0.1:8001/items |

**Typical browser flow:**

1. Open `/shop/register/` → create account (logged in automatically).
2. Go to `/shop/items/new/` → add an item.
3. Browse `/shop/items/` and open an item detail page.
4. Compare the same data at `/items` (JSON).

---

## Tests

Shop pages are covered in **`tests/test_shop.py`** (pytest-django `Client`, not `APIClient`):

- Home and list pages render
- Item detail shows API-created items
- Create requires login; logged-in create works
- Register creates user and session
- Duplicate email shows form error

```bash
pytest tests/test_shop.py -v
```

---

## Explore the JSON API in the browser

The shop is not the full API. For FastAPI-style interactive docs, use **Swagger UI** at `/docs` — see **[api-docs.md](api-docs.md)**.

---

## Should the frontend call the API?

**Not in this project.** Reasons:

- Same codebase — no separate SPA or mobile client yet.
- Direct service calls are simpler, faster, and idiomatic for server-rendered Django.
- Calling your own API from templates would mean JWT in the browser, CORS, fetch error handling, and duplicating validation in forms *and* serializers.

**When API-first frontend *does* make sense:** separate React/Vue app, mobile apps, or multiple teams/clients sharing one API. A good next exercise is a **small SPA on another port** that calls `/items` — without rewriting the shop to fetch itself.

---

## Possible extensions

Not implemented yet; natural next steps if you want to go deeper:

- Edit/delete items in the browser (`UpdateView` / `DeleteView`)
- Category browse pages
- HTMX for partial page updates without a full SPA
- Shared validation between DRF serializers and forms (DRF is not required for that — custom validators or service-layer checks work too)
