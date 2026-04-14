# AGENTS.md

## Project Shape
- Personal-use app. Do not reintroduce login/auth flows.
- Frontend is a single Jobs screen (`frontend/src/App.tsx` renders `Jobs` directly).
- Backend app entrypoint is `backend.main:app`.
- Source of truth for preferences is `portfolio.md`; update that file instead of hard-coding matching rules.

## Runtime Behavior
- Backend creates the schema on startup (`Base.metadata.create_all`) and starts the scheduler automatically.
- Scheduler fetches jobs every 6h and scans alerts every 24h.
- Alert statuses are `unread`, `read`, and `ready`.
- Copying an alert draft marks it `ready` in the UI.

## Commands
- Local backend: `uvicorn backend.main:app --reload`
- Local frontend: `cd frontend && npm run dev`
- Docker stack: `docker compose up --build`
- Backend tests: `docker compose run --rm backend pytest tests -q`
- Single backend test file: `docker compose run --rm backend pytest tests/test_alerts.py -q`
- Frontend build: `docker compose run --rm frontend npm run build`
- Frontend lint: `cd frontend && npm run lint`

## Docker / Data
- Docker backend image copies `README.md`, `pyproject.toml`, `portfolio.md`, `backend/`, and `tests/`.
- Docker Compose uses the named volume `jobcodex_data` for SQLite state.
- If you change backend code, `portfolio.md`, or tests, rebuild the backend image before assuming Docker is using your edits.

## Editing Rules
- Keep changes small; this repo is currently a compact jobs tracker, not a multi-page product.
- Preserve the in-app alerts queue and the ready/read flow when touching frontend code.
- Treat `portfolio.md` as the user’s live preference profile when changing matching or scan logic.
