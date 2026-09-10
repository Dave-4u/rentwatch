# RentWatch

Property rent tracking for a single landlord (Mr Eli Stephen), approved agents, and tenants. Physical payments only — no online checkout.

## Features

- Sole landlord (seeded). Agents and tenants register and wait for approval.
- Properties (up to ~100) with types: Self, One bedroom, Two bedroom, Three bedroom, Store, Duplex.
- Monthly leases with due day (1–28), rent in NGN.
- Staff record cash/transfer/other payments; tenants see history and balance.
- Overdue detection for unpaid periods after the due date, with in-app notifications.

## Requirements

- Python 3.11+ (3.12/3.13 fine)
- Node.js 18+ and npm
- Windows, macOS, or Linux

## Quick start

### 1. Backend

```bash
cd rentwatch
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r backend/requirements.txt
copy .env.example .env
# (Windows) or: cp .env.example .env

# Seed landlord (also runs automatically on API startup)
python -m backend.seed

# Run API (from project root)
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

API docs: http://127.0.0.1:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173 — Vite proxies API calls to port 8000.

### 3. Tests

```bash
# from project root, venv active
pytest
```

## Seed landlord

| Field    | Value                      |
|----------|----------------------------|
| Email    | `landlord@rentwatch.local` |
| Password | `ChangeMe123!`             |
| Name     | Mr Eli Stephen             |

**Change this password after first login in production.**

Nobody can register as landlord. New agents/tenants stay `pending` until the landlord or an approved agent approves them. Pending users get HTTP 403 on dashboards and see a waiting screen.

## Project layout

```
rentwatch/
  backend/          FastAPI + SQLAlchemy + SQLite
  frontend/         React + TypeScript + Vite PWA
  data/             SQLite database file (created at runtime)
  .env.example
  README.md
```

## Demo flow

1. Sign in as landlord.
2. Register an agent and a tenant in another browser/session; approve them under Approvals.
3. Create a property, then a lease linking the tenant.
4. After the due day (or set due_day in the past for demos), overdue appears on dashboards; tenant gets a notification.
5. Record a physical payment under Pay; balance clears when period payments cover rent.

## Notes

- Database default: `./data/rentwatch.db` relative to the project root.
- JWT secret and CORS are configurable via environment variables (see `.env.example`).
- Built for client demos — keep the repo private and rotate credentials before any public deploy.
