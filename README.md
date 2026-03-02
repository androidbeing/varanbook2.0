# Varanbook – Matrimonial SaaS Platform

A multi-tenant matrimonial platform built with **FastAPI** (backend) and **Vue 3 + Vuetify** (frontend).

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Structure](#project-structure)
3. [Backend Setup (FastAPI)](#backend-setup-fastapi)
4. [Frontend Setup (Vue 3)](#frontend-setup-vue-3)
5. [Running with Docker Compose](#running-with-docker-compose)
6. [Environment Variables](#environment-variables)
7. [Database Migrations](#database-migrations)
8. [Running Tests](#running-tests)

---

## Prerequisites

| Tool | Minimum Version |
|------|----------------|
| Python | 3.11+ |
| Node.js | 18+ |
| npm | 9+ |
| PostgreSQL | 15+ (or Docker) |
| Docker & Docker Compose | Latest stable |

---

## Project Structure

```
varanbook/
├── app/                  # FastAPI backend
│   ├── main.py
│   ├── config.py         # Settings (reads from .env)
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   └── services/
├── frontend/             # Vue 3 + Vuetify frontend
│   ├── src/
│   └── package.json
├── alembic/              # Database migrations
├── tests/                # Pytest test suite
├── docker-compose.yml    # Full local stack (API, DB, Redis, LocalStack)
└── requirements.txt
```

---

## Backend Setup (FastAPI)

### 1. Create and activate a virtual environment

```powershell
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 2. Install Python dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example below into a `.env` file at the project root and fill in the values:

```env
# App
APP_ENV=development
DEBUG=true
SECRET_KEY=your-secret-key-change-in-production

# Database (asyncpg connection string)
DATABASE_URL=postgresql+asyncpg://varanbook_admin:devpassword123@localhost:5432/varanbook

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# AWS (use LocalStack values for local dev)
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=localstack
AWS_SECRET_ACCESS_KEY=localstack
S3_BUCKET_NAME=varanbook-media-dev
SQS_NOTIFICATION_QUEUE_URL=http://localhost:4566/000000000000/varanbook-notifications-dev

# CORS – must include the frontend URL
ALLOWED_ORIGINS=["http://localhost:5173"]

# Email (optional for local dev)
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM=noreply@example.com
APP_FRONTEND_URL=http://localhost:5173
```

### 4. Apply database migrations

Ensure PostgreSQL is running first (via Docker or a local install), then:

```powershell
alembic upgrade head
```

### 5. Start the backend dev server

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at **http://localhost:8000**.  
Interactive docs: **http://localhost:8000/docs**  
ReDoc: **http://localhost:8000/redoc**

---

## Frontend Setup (Vue 3)

### 1. Install Node dependencies

```powershell
cd frontend
npm install
```

### 2. Start the frontend dev server

```powershell
npm run dev
```

The app will be served at **http://localhost:5173**.

### Other frontend scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server with hot-reload |
| `npm run build` | Type-check and build for production |
| `npm run preview` | Preview the production build locally |
| `npm run type-check` | Run TypeScript type checking only |

---

## Running with Docker Compose

The `docker-compose.yml` spins up the full local stack:
- **PostgreSQL 15** on port `5432`
- **Redis 7** on port `6379`
- **LocalStack** (S3, SQS, Secrets Manager) on port `4566`
- **FastAPI** on port `8000` (with auto-reload and auto-migration)

```powershell
# Build and start all services
docker compose up --build

# Run in the background
docker compose up -d --build

# Stop all services
docker compose down

# Destroy volumes (wipes DB data)
docker compose down -v
```

> **Note:** The frontend is not included in Docker Compose for local development. Run `npm run dev` separately in the `frontend/` directory.

---

## Environment Variables

All backend settings are defined in `app/config.py` and loaded via `pydantic-settings` from the `.env` file or real environment variables. Required variables with no defaults:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Secret used to sign JWTs |
| `DATABASE_URL` | AsyncPG PostgreSQL connection string |

---

## Database Migrations

Migrations are managed with **Alembic**.

```powershell
# Apply all pending migrations
alembic upgrade head

# Roll back the last migration
alembic downgrade -1

# Generate a new migration (after changing models)
alembic revision --autogenerate -m "describe_your_change"

# Show current migration state
alembic current
```

---

## Running Tests

```powershell
# Run the full test suite
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_users.py
```
