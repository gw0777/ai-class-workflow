# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Layout

This is a two-part app: a FastAPI backend (`backend/`) and an Expo / React Native mobile client (`mobile/`). They are developed together but run as separate processes. There is also `ARCHITECTURE.md` (system overview, data model, API surface) and several Korean PE-curriculum reference PDFs/PPTX at the repo root that are domain context, not code.

## Common Commands

### Backend (`backend/`)

```bash
# Start Postgres + Redis (must be running before the API)
docker-compose up -d

# One-time setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit SECRET_KEY, OPENAI_API_KEY

# Run the API (from backend/app, NOT from backend/)
cd app && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
# OpenAPI docs: http://localhost:8000/docs
```

There is no test suite or linter configured yet.

### Mobile (`mobile/`)

```bash
npm install
npm start          # Expo dev server
npm run ios        # iOS simulator
npm run android    # Android emulator
```

`API_BASE_URL` is hardcoded in `src/services/api.js` as `http://localhost:8000/api/v1`. When running on a device/emulator, change it (Android emulator uses `http://10.0.2.2:8000/api/v1`; physical device needs the host LAN IP).

## Architecture Notes

### Backend structure
- `app/main.py` — FastAPI app factory, CORS, and router mounting under `/api/v1/*`. Currently mounts `auth`, `activities`, `users`, and `documents`. The `locations` and `analysis` routers referenced in `ARCHITECTURE.md` are **not yet implemented** (TODO comment in `main.py`). Lifespan also `mkdir`s `settings.UPLOAD_DIR` on startup.
- `app/database.py` — Maintains both an **async engine** (`asyncpg`, used by request handlers via the `get_db` dependency) and a **sync engine** (`psycopg2`, intended for Alembic). `get_db` auto-commits on successful yield and rolls back on exception — handlers should not call `db.commit()` themselves for the happy path.
- `app/config.py` — Pydantic `BaseSettings` reads `backend/.env`. `DATABASE_URL` (async) and `DATABASE_URL_SYNC` are required and have no defaults; the app will fail to import without them.
- `app/main.py` lifespan calls `create_tables()` only when `DEBUG=True`. There are no Alembic migrations checked in yet despite the sync engine being set up for them — schema currently comes from `Base.metadata.create_all`.
- `app/services/auth.py` — JWT auth (HS256). `get_current_user` is the FastAPI dependency for protected routes; tokens carry `sub=user_id` and a `type` of `access` or `refresh`. Access token TTL 15 min, refresh 7 days.
- `app/models/` — SQLAlchemy 2.0 models: `User`, `ActivityLog`, `LocationContext`, `UserInput`, `AnalysisReport`, `LocationCluster`, `Document`. All keyed by UUID. See `ARCHITECTURE.md` for field-by-field breakdown (note: `Document` is newer and not yet in `ARCHITECTURE.md`).
- `app/services/hwp_extractor.py` — Plain-text extraction for HWP/HWPX. HWPX is parsed with stdlib `zipfile` + `ElementTree` against the `hp:` namespace (`hp:p` per-paragraph, `hp:t` for runs). HWP (binary OLE) only reads the `PrvText` preview stream via `olefile` — **full body parsing is intentionally out of scope**; if `PrvText` is absent the upload still succeeds but `extraction_error` is set on the `Document` row. Uploaded files live under `settings.UPLOAD_DIR/{user_id}/{uuid}.{ext}`.

### Mobile structure
- `App.js` wraps the navigator in three providers in this order: `PaperProvider` → `AuthProvider` → `NotificationProvider`. Auth state must be available before notifications because notification scheduling depends on the logged-in user.
- `src/contexts/AuthContext.js` is the source of truth for the current user; `src/services/api.js` reads/writes the JWT pair from `AsyncStorage` (`accessToken`, `refreshToken`).
- The axios instance in `api.js` has a response interceptor that transparently calls `/auth/refresh` on 401 once, then retries the original request. On refresh failure it clears stored credentials — UI code should listen for the resulting auth state change rather than handling 401s itself.
- Login uses `multipart/form-data` (FastAPI's OAuth2 form), not JSON — keep that in mind when adding new auth flows.
- Screens live in `src/screens/`; navigation graph in `src/navigation/AppNavigator.js`.

### Cross-cutting concerns
- API base path is `/api/v1`. Any new router must be mounted in `app/main.py` and a matching client added in `mobile/src/services/api.js`.
- Default timezone is `Asia/Seoul` (config + UI assume this); any time arithmetic should respect it.
- The OpenAI integration (insights/analysis) is planned but not wired up — `OPENAI_API_KEY` is read from settings but no service consumes it yet.
