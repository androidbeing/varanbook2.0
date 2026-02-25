# Varanbook 2.0 – Matrimonial SaaS Platform

A multi-tenant matrimonial platform built with **FastAPI** (backend) and **Vue 3 + Vuetify** (frontend).

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| npm | 9+ |
| PostgreSQL | 15 (or Docker) |
| Redis | 7 (or Docker) |

---

## 1. Environment Setup

Create a `.env` file in the project root:

```env
# App
APP_ENV=development
DEBUG=true
SECRET_KEY=your-super-secret-key-change-me

# Database (async)
DATABASE_URL=postgresql+asyncpg://varanbook_admin:devpassword123@localhost:5432/varanbook

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# AWS (use LocalStack for local dev)
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
S3_BUCKET_NAME=varanbook-media

# CORS – allow the Vite dev server
ALLOWED_ORIGINS=["http://localhost:5173"]
```

---

## 2. Option A – Start with Docker (Recommended for first run)

Spins up PostgreSQL, Redis, LocalStack, and the API together:

```powershell
docker compose up --build
```

The API will be available at **http://localhost:8000**.

To run only the infrastructure (DB + Redis) and start the API manually:

```powershell
docker compose up db redis -d
```

---

## 3. Option B – Start Manually (Development)

### 3.1 Backend – FastAPI

**Create and activate virtual environment:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Install dependencies:**

```powershell
pip install -r requirements.txt
```

**Apply database migrations:**

```powershell
alembic upgrade head
```

**Start the FastAPI server:**

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API root:** http://localhost:8000
- **Interactive docs (Swagger):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

### 3.2 Frontend – Vue 3 + Vite

Open a **new terminal**, then:

```powershell
cd frontend
npm install
npm run dev
```

The Vue app will be available at **http://localhost:5173**

---

## 4. Running Both Together (Quick Reference)

Open two separate terminals:

**Terminal 1 – Backend:**
```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 – Frontend:**
```powershell
cd frontend
npm run dev
```

---

## 5. Other Useful Commands

### Run Tests
```powershell
.\.venv\Scripts\Activate.ps1
pytest
```

### Seed Superadmin
```powershell
python scripts/seed_superadmin.py
```

### Build Frontend for Production
```powershell
cd frontend
npm run build
```

### Create a New Alembic Migration
```powershell
alembic revision --autogenerate -m "describe_your_change"
alembic upgrade head
```

---

## 6. Project Structure

```
varanbook/
├── app/                  # FastAPI application
│   ├── main.py           # App factory & lifespan
│   ├── config.py         # Settings (loaded from .env)
│   ├── database.py       # Async SQLAlchemy engine
│   ├── auth/             # JWT auth & dependencies
│   ├── middleware/        # Tenant, audit, rate-limit
│   ├── models/           # SQLAlchemy ORM models
│   ├── routers/          # API route handlers
│   ├── schemas/          # Pydantic request/response schemas
│   └── services/         # Email, S3, notifications
├── frontend/             # Vue 3 + Vuetify SPA
│   └── src/
│       ├── api/          # Axios API clients
│       ├── views/        # Page-level components
│       ├── stores/       # Pinia state stores
│       └── router/       # Vue Router config
├── alembic/              # Database migrations
├── tests/                # Pytest test suite
├── terraform/            # AWS infrastructure (IaC)
├── docker-compose.yml    # Local dev stack
└── requirements.txt      # Python dependencies
```

---

## 7. Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy (async), asyncpg |
| Auth | python-jose (JWT), passlib (bcrypt) |
| Database | PostgreSQL 15 |
| Cache / Queue | Redis, Celery |
| Storage | AWS S3 (LocalStack locally) |
| Frontend | Vue 3, Vuetify 3, Pinia, Vue Router, Vite |
| Testing | pytest, pytest-asyncio, httpx |
| Infrastructure | Terraform, AWS Lambda / RDS / API Gateway |
