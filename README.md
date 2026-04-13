# JobCodex

Job copilot for discovery, matching, tailoring, and tracking.

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

## Features

- **Auth**: JWT-based registration/login
- **Profile**: Target roles, locations, seniority preferences
- **Resumes**: Upload PDF/DOCX, auto-parse
- **Jobs**: Add Greenhouse/Lever/Ashby sources, search
- **Matching**: Score jobs against your profile
- **Tailoring**: AI-powered resume bullets & cover letters
- **Tracking**: Pipeline view, status updates, tasks

## API

The backend runs at http://localhost:8000 with Swagger docs at /docs.

## Testing

```bash
pytest tests/ -v
```

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL/SQLite
- **Frontend**: React, Vite, Tailwind CSS, TypeScript
- **AI**: OpenAI GPT-4o-mini (optional)
