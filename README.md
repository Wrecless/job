# JobCodex

Personal jobs tracker for reviewing open jobs and marking whether they have been applied to.

## Quick Start

```bash
# Install backend dependencies
pip install -e ".[dev]"

# Install frontend dependencies
cd frontend && npm install && cd ..

# Start backend (in one terminal)
uvicorn backend.main:app --reload

# Start frontend (in another terminal)
cd frontend && npm run dev
```

Open http://localhost:5173 to see the app.

## Docker

```bash
docker compose up --build
```

Then open http://localhost:5173.

The backend SQLite database is stored in the named Docker volume `jobcodex_data`.

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Optional: Enable AI-powered tailoring
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini

# Database (defaults to SQLite)
DATABASE_URL=sqlite+aiosqlite:///./jobcodex.db
```

Without OpenAI API key, the app falls back to template-based content generation.

The app runs in personal mode by default and creates a single local user automatically.

## Features

- **Personal mode**: No login required, single-user local access
- **Jobs**: View jobs and mark them applied or not applied
- **Tracking**: Simple application status list

## API

The backend runs at http://localhost:8000.

## Testing

```bash
docker compose run --rm backend pytest tests/ -v
```

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL/SQLite
- **Frontend**: React, Vite, Tailwind CSS, TypeScript
- **AI**: OpenAI GPT-4o-mini (optional)
