# RentWatch

Property rent tracking for a single landlord (Mr Eli Stephen), approved agents, and tenants. Physical payments only — no online checkout.

## Public demo links

| What | URL | Status |
|------|-----|--------|
| **Shareable frontend (GitHub Pages)** | https://dave-4u.github.io/rentwatch/ | **Live** (static UI; API not wired until Render + `VITE_API_URL`) |
| **API + full app (Render)** | *(not deployed yet)* | Parent: deploy via Render Dashboard Blueprint — see below |

Until `VITE_API_URL` points at a live Render service, the Pages site loads but API calls fail. Prefer the **single-origin Render URL** once deployed (one link serves UI + API).

Pages is currently published from the `gh-pages` branch. The Actions workflow (`.github/workflows/pages.yml`) is in the working tree; pushing it requires a GitHub token with the `workflow` scope (`gh auth refresh -s workflow`).

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

## Quick start (local)

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

### 3. Single-origin production (local)

```bash
cd frontend && npm run build && cd ..
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

FastAPI serves `frontend/dist` for non-API routes (SPA fallback). Leave `VITE_API_URL` empty so the UI calls the same origin.

### 4. Tests

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

Nobody can register as landlord. New agents/tenants stay `pending` until the landlord or an approved agent approves them.

## Deploy

### A. Render (API + UI, recommended share link)

1. Push this repo to GitHub (already public).
2. In [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**, connect `Dave-4u/rentwatch` and apply `render.yaml`.
   - Or **New** → **Web Service** → Docker from this repo; name `rentwatch`.
3. Env (Blueprint sets these; override as needed):
   - `SECRET_KEY` — auto-generated on Blueprint, or set a long random string
   - `CORS_ORIGINS=*` (or include `https://dave-4u.github.io`)
   - `DATABASE_URL=sqlite:////tmp/rentwatch.db`
4. After deploy, open `https://<service>.onrender.com/health` — expect `{"status":"ok",...}`.
5. That same URL serves the full app (UI + API). Send **that** link to Mr Stephen.

**Warning:** Free Render disks are ephemeral. SQLite under `/tmp` **resets on every restart/redeploy**. Demo data (including seed) is re-created on startup; do not rely on persistence for production.

Render CLI is optional; browser Blueprint/Web Service is enough.

### B. GitHub Pages (frontend only)

Shareable UI (verified): **https://dave-4u.github.io/rentwatch/**

**Current setup:** legacy Pages from branch `gh-pages` (already enabled). Rebuild/push that branch after frontend changes, or switch to Actions once the workflow file is on `main`.

1. Repo is **public** (required for free Pages).
2. Optional Actions path: Settings → Pages → Source: **GitHub Actions** after `.github/workflows/pages.yml` is pushed (needs `workflow` OAuth scope).
3. Set repository **variable** (Settings → Secrets and variables → Actions → Variables):
   - Name: `VITE_API_URL`
   - Value: your Render origin with **no trailing slash**, e.g. `https://rentwatch.onrender.com`
4. Rebuild Pages with `VITE_PAGES=true` and that API URL, then update `gh-pages` (or let the Actions workflow deploy).
5. Pages builds with `base: '/rentwatch/'` and calls the Render API via `VITE_API_URL`.

Until `VITE_API_URL` is set, the static site still deploys but cannot reach the API.

Docker / same-origin builds use `base: '/'` and empty `VITE_API_URL` (see `Dockerfile`).

### C. Render CLI

Render CLI is **not** available in this environment (no `render` binary, no Docker). Finish API deploy in the browser: [dashboard.render.com](https://dashboard.render.com) → New → Blueprint → select `Dave-4u/rentwatch` → apply `render.yaml`.

### CORS

`CORS_ORIGINS` is a comma-separated list (see `.env.example`). Defaults include localhost and `https://dave-4u.github.io`. Use `*` to allow any origin (credentials middleware is disabled when `*` is used).

## Project layout

```
rentwatch/
  backend/                 FastAPI + SQLAlchemy + SQLite
  frontend/                React + TypeScript + Vite PWA
  Dockerfile               Multi-stage Node build + Python/uvicorn
  render.yaml              Render Blueprint (free Web Service)
  .github/workflows/       GitHub Pages deploy
  data/                    Local SQLite (created at runtime)
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

- Local DB default: `./data/rentwatch.db` relative to the project root.
- JWT secret and CORS are configurable via environment variables (see `.env.example`).
- Built for client demos — rotate the seed password and `SECRET_KEY` before sharing widely.
