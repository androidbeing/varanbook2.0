# Varanbook â€“ Matrimonial SaaS Platform

A multi-tenant matrimonial platform built with **FastAPI** (backend) and **Vue 3 + Vuetify** (frontend).

---

## Table of Contents

- [Varanbook â€“ Matrimonial SaaS Platform](#varanbook--matrimonial-saas-platform)
  - [Table of Contents](#table-of-contents)
  - [Prerequisites](#prerequisites)
  - [Project Structure](#project-structure)
  - [Backend Setup (FastAPI)](#backend-setup-fastapi)
    - [1. Create and activate a virtual environment](#1-create-and-activate-a-virtual-environment)
    - [2. Install Python dependencies](#2-install-python-dependencies)
    - [3. Configure environment variables](#3-configure-environment-variables)
    - [4. Apply database migrations](#4-apply-database-migrations)
    - [5. Start the backend dev server](#5-start-the-backend-dev-server)
  - [Frontend Setup (Vue 3)](#frontend-setup-vue-3)
    - [1. Install Node dependencies](#1-install-node-dependencies)
    - [2. Start the frontend dev server](#2-start-the-frontend-dev-server)
    - [Other frontend scripts](#other-frontend-scripts)
  - [Running with Docker Compose](#running-with-docker-compose)
  - [Environment Variables](#environment-variables)
  - [Database Migrations](#database-migrations)
  - [Running Tests](#running-tests)

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
â”œâ”€â”€ app/                  # FastAPI backend
â”‚   â”œâ”€â”€ main.py
â”‚   â”œâ”€â”€ config.py         # Settings (reads from .env)
â”‚   â”œâ”€â”€ models/
â”‚   â”œâ”€â”€ routers/
â”‚   â”œâ”€â”€ schemas/
â”‚   â””â”€â”€ services/
â”œâ”€â”€ frontend/             # Vue 3 + Vuetify frontend
â”‚   â”œâ”€â”€ src/
â”‚   â””â”€â”€ package.json
â”œâ”€â”€ alembic/              # Database migrations
â”œâ”€â”€ tests/                # Pytest test suite
â”œâ”€â”€ docker-compose.yml    # Full local stack (API, DB, Redis, LocalStack)
â””â”€â”€ requirements.txt
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

# CORS â€“ must include the frontend URL
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

---

## Production Deployment

### Architecture

| Layer | Service |
|-------|---------|
| Backend API | AWS Lightsail Container Service (Docker / Gunicorn + FastAPI) |
| Frontend SPA | AWS S3 + CloudFront CDN |
| Database | AWS RDS PostgreSQL |
| Media Storage | AWS S3 (`varanbook-media-production`) |
| Infrastructure | Terraform (manages all the above) |

---

### One-Time Setup

#### 1. Install required tools

```powershell
winget install Amazon.AWSCLI Hashicorp.Terraform
# Docker Desktop must be installed and RUNNING
```

Configure your AWS CLI credentials:

```powershell
aws configure
# Enter: Access Key ID, Secret Access Key, region (ap-south-1), output (json)
```

#### 2. Configure Terraform variables

```powershell
Copy-Item terraform\terraform.tfvars.example terraform\terraform.tfvars
```

Open `terraform\terraform.tfvars` and fill in all values:

```hcl
aws_region     = "ap-south-1"
project_name   = "varanbook"
environment    = "production"

db_host        = "your-rds-endpoint.rds.amazonaws.com"
db_port        = 5432
db_name        = "postgres"
db_username    = "postgres"
db_password    = "your-db-password"

app_secret_key = "your-strong-secret-key"

smtp_host      = ""
smtp_port      = 587
smtp_username  = ""
smtp_password  = ""
smtp_from      = "noreply@yourdomain.com"
```

#### 3. Bootstrap infrastructure (first time only)

```powershell
.\scripts\deploy.ps1 -Bootstrap
```

This runs `terraform init` + `terraform apply` to provision the Lightsail container service, S3 buckets, and CloudFront distribution.

---

### Deploying Changes

All deployments are driven by `scripts\deploy.ps1`.

#### Deploy everything (backend + frontend)

```powershell
.\scripts\deploy.ps1
```

What it does:
1. Runs `terraform apply` to sync any infrastructure changes.
2. Builds a Docker image of the FastAPI app.
3. Pushes the image to the Lightsail Container Service.
4. Creates a new Lightsail deployment and polls until it becomes `ACTIVE`.
5. Builds the Vue.js frontend (`npm run build`) with `VITE_API_BASE_URL` set to the live API URL.
6. Syncs `frontend/dist/` to the S3 bucket with long-lived cache headers.
7. Uploads `index.html` separately with `no-cache` headers.
8. Creates a CloudFront invalidation so users receive the new build immediately.

#### Deploy backend (FastAPI) only

Use after changing Python code, adding a router, updating `requirements.txt`, or running a new migration:

```powershell
.\scripts\deploy.ps1 -SkipFrontend
```

#### Deploy frontend (Vue) only

Use after changing files under `frontend/src/` with no backend changes:

```powershell
.\scripts\deploy.ps1 -SkipBackend
```

---

### Applying Database Migrations on the Server

Migrations are **not** run automatically on deployment. Run them manually from your local machine against the production RDS instance before (or immediately after) pushing a backend image that includes model changes.

```powershell
# Set production DB URL for this session
$env:DATABASE_URL = "postgresql+asyncpg://postgres:<password>@<rds-endpoint>:5432/postgres"

# Apply all pending migrations
.venv\Scripts\python.exe -m alembic upgrade head

# Confirm current revision
.venv\Scripts\python.exe -m alembic current
```

> **Rule of thumb:** always run `alembic upgrade head` **before** or **immediately after** each backend deployment that adds new DB columns. Skipping this causes 500 errors because the ORM references columns that do not yet exist in the database.

---

### Standard Change Workflow

```
1. Edit code locally
2. Test with:  uvicorn --reload  +  npm run dev
3. If SQLAlchemy models changed:
     a. .venv\Scripts\python.exe -m alembic revision --autogenerate -m "what changed"
     b. Review the generated file in alembic/versions/
     c. Apply to production DB (see section above)
4. Deploy backend:    .\scripts\deploy.ps1 -SkipFrontend
5. Deploy frontend:   .\scripts\deploy.ps1 -SkipBackend
   (or both at once:  .\scripts\deploy.ps1)
```

---

### S3 Bucket — CORS Configuration

The `varanbook-media-production` bucket requires a CORS rule so the browser can PUT files directly via presigned URLs.

**cors.json**
```json
[
  {
    "AllowedHeaders": ["Content-Type"],
    "AllowedMethods": ["PUT", "GET"],
    "AllowedOrigins": [
      "https://your-cloudfront-domain.cloudfront.net",
      "http://localhost:5173"
    ],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }
]
```

Apply with the CLI:

```powershell
aws s3api put-bucket-cors `
  --bucket varanbook-media-production `
  --cors-configuration file://cors.json `
  --region ap-south-1
```

> **Presigned PUT 403 note:** The S3 presigned PUT URL signs only `content-type` and `host` headers. Do **not** include `ServerSideEncryption` in the boto3 presign `Params` — doing so adds `x-amz-server-side-encryption` to `SignedHeaders`, and the browser PUT will return 403 Forbidden if that header is absent. Bucket-level SSE-S3 (enabled by default since Jan 2023) handles encryption at rest without any client-side headers.

---

### IAM Permissions Required

The IAM user whose credentials are in `.env` must have:

```json
{
  "Effect": "Allow",
  "Action": [
    "s3:PutObject",
    "s3:GetObject",
    "s3:DeleteObject"
  ],
  "Resource": "arn:aws:s3:::varanbook-media-production/*"
}
```

---

### Monitoring & Troubleshooting

| Task | Where |
|------|-------|
| Live API logs | AWS Console → Lightsail → `varanbook-api-production` → Deployments → Logs |
| Check deployment state | `aws lightsail get-container-service-deployments --service-name varanbook-api-production --region ap-south-1` |
| Check CloudFront invalidation | `aws cloudfront list-invalidations --distribution-id <DIST_ID>` |
| Rollback backend | `git checkout <sha>` then `.\scripts\deploy.ps1 -SkipFrontend` |
| Rollback DB migration | `.venv\Scripts\python.exe -m alembic downgrade -1` then redeploy |
