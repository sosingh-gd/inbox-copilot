# Inbox Copilot backend

FastAPI service for Google sign-in, read-only Gmail and Google Calendar access, and a
Claude-powered chat that streams replies over Server-Sent Events.

## Setup

1. In Google Cloud, create an OAuth client of type **Web application**, add
   `http://localhost:5173` as an authorized JavaScript origin (the popup flow uses
   `redirect_uri=postmessage`, so no redirect URI is needed), configure the consent screen with
   test users, and enable the Gmail and Google Calendar APIs.
2. Install and configure:

   ```bash
   make install
   cp .env.example .env
   uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

   Put the generated key, the Google client credentials and your Anthropic API key in `.env`.

3. Run it: `make dev` (API on <http://localhost:8000>, docs at <http://localhost:8000/api/docs>).

Run `make` to see every command. `make check` (format, lint, strict mypy) must pass before
committing.

## Layout

```text
app/
├── main.py              # create_app(): routers, error handlers, lifespan (DB + Anthropic client)
├── core/                # config, errors (RFC 9457 Problem Details), security, SSE helpers
├── db/                  # engine/session lifecycle, Base, model registry (db/models.py)
├── api/                 # shared dependencies (SessionDep, CurrentUser), v1 router
├── agents/              # AgentRunner (tool-use loop), email/calendar/weather agents, orchestrator, prompts/
├── features/
│   ├── auth/            # Google OAuth, sessions, encrypted refresh tokens (HTTP: /auth)
│   ├── chat/            # conversations + SSE stream that runs the agents (HTTP: /chat)
│   ├── emails/          # agent tools only: EmailSource protocol + Gmail implementation
│   ├── calendar/        # agent tools only: CalendarSource protocol + Google Calendar implementation
│   └── weather/         # agent tools only: WeatherSource protocol + Open-Meteo implementation
└── scripts/export_openapi.py
```

Only `auth` and `chat` expose HTTP endpoints. The data features (`emails`, `calendar`, `weather`)
have no router or service: they provide a `Source` plus the `tools.py` the agents call.

Features use this split (each one has only the files it needs):

| File | Responsibility |
| --- | --- |
| `router.py` | HTTP only: parse the request, call the service, return a schema |
| `schemas.py` | Pydantic request/response models (the API contract, camelCase on the wire) |
| `service.py` | Business rules. Never imports FastAPI; raises errors from `core/errors.py` |
| `repository.py` | SQLAlchemy queries |
| `models.py` | ORM tables (also import them in `db/models.py`) |
| `sources.py` | Adapters for external systems, behind a `Protocol` so local fake data can stand in for them |
| `tools.py` | Agent tools built on a source (Pydantic input model + async handler) |
| `deps.py` | Wires the above together for FastAPI's dependency injection |

## Adding an endpoint

1. Add schemas, then service/repository logic, then a thin route in the feature's `router.py`.
   New features get their router included in `app/api/v1/router.py`.
2. From the repo root, run `make api` to regenerate `contract/openapi.json` and the frontend's
   TypeScript types.

## Security notes

- Google tokens never reach the browser. Refresh tokens are encrypted in SQLite, and only SHA-256
  hashes of session IDs are stored.
- State-changing requests must send `X-Requested-With: XmlHttpRequest` (CSRF protection, together
  with `SameSite=Lax` cookies).
- Gmail and Calendar access is read-only. Chat system prompts treat email content as untrusted.
