# AGENTS.md

## Repo Shape
- Personal-use app. Do not reintroduce login/auth flows.
- Frontend is a single Jobs screen: `frontend/src/app/page.tsx` renders the client `Jobs` component from `frontend/src/components/Jobs.tsx`.
- Backend entrypoint is `backend.main:app`.
- `portfolio.md` is the source of truth for matching preferences and source filters; do not hard-code those rules elsewhere.

## Runtime
- Backend creates tables on startup and seeds starter sources automatically.
- Scheduler starts with the app: job fetch every 6h, alert scan every 24h.
- SQLite lives in the Docker named volume `jobcodex_data`; stale source/job state can persist between runs.
- Alert statuses are `unread`, `read`, and `ready`; copying a draft marks it `ready` in the UI.
- Frontend reads `NEXT_PUBLIC_API_URL` in `frontend/src/api.ts`; do not use the old Vite env name.

## Commands
- Backend dev server: `uvicorn backend.main:app --reload`
- Frontend dev server: `cd frontend && npm run dev` (Next on `5173`)
- Full stack: `docker compose up --build`
- Backend tests: `docker compose run --rm backend pytest tests -q`
- Focused backend test: `docker compose run --rm backend pytest tests/test_alerts.py -q`
- Frontend build: `docker compose run --rm frontend npm run build`
- Frontend lint: `cd frontend && npm run lint`

## Docker / Workflow
- Docker backend image copies `README.md`, `pyproject.toml`, `portfolio.md`, `backend/`, and `tests/`.
- If you change backend code, `portfolio.md`, or tests, rebuild the backend image before trusting Docker results.
- Frontend API base URL comes from `NEXT_PUBLIC_API_URL` and defaults to `http://localhost:8000`.
