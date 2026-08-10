# Holiday Home ERP

A holiday-home / property management ERP. v1 build in progress — see
`docs/holiday-home-erp-v1-build-plan.pdf` for the full plan (scope, database schema, API
design, and what's deliberately deferred: auth/roles and automated tests, plan §7).

**What's actually functional right now:** Units, Buildings, and Landlords & Counterparties
have full backend CRUD + real frontend grids/forms, including the relationships between
them (a unit has exactly one building and one-or-more landlords). Every other item in the
sidebar is a working route with a real grid/form UI, but its backend doesn't exist yet —
those grids will show a connection error until their module is built.

---

## 1. Prerequisites

- **Python 3.12**
- **Node.js** (v20+) and npm
- **PostgreSQL 16** — see step 2 for setup, or use Docker instead (step 2b)

---

## 2. Set up the database

### 2a. Install PostgreSQL directly (recommended if you don't already use Docker)

Download from https://www.postgresql.org/download/windows/ (EDB installer). During setup
you'll set a password for the `postgres` superuser — remember it, you'll need it once.

Once installed, open the Start menu → **SQL Shell (psql)** → press Enter through the
prompts (Server/Database/Port/Username) until it asks for a password, then enter your
postgres superuser password. At the `postgres=#` prompt, run:

```sql
CREATE USER erp WITH PASSWORD 'erp';
CREATE DATABASE holiday_home_erp OWNER erp;
```

You should see `CREATE ROLE` then `CREATE DATABASE`. Type `\q` to exit.

### 2b. Or: use Docker instead

Install Docker Desktop, then skip straight to `docker compose up --build` from the repo
root — it starts Postgres, the API, and the frontend together. Everything below still
applies if you want to run the pieces individually instead.

---

## 3. Backend setup

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment (pick your shell):
```bash
# Git Bash
source .venv/Scripts/activate
# PowerShell
.venv\Scripts\Activate.ps1
# cmd.exe
.venv\Scripts\activate.bat
```
Your prompt should now start with `(.venv)`. If activation fails (e.g. PowerShell
execution policy), skip it and just prefix every command below with the venv's path —
e.g. `.venv/Scripts/python -m ...` and `.venv/Scripts/alembic ...` instead of
`python ...` / `alembic ...`.

```bash
pip install -r requirements.txt
cp .env.example .env
# only edit .env if your Postgres user/password/port differ from erp/erp/5432
```

Create and apply the database schema:
```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

Seed the Chart of Accounts and reference data (safe to re-run; skips what already exists):
```bash
python -m app.seed.run
```

Start the API:
```bash
uvicorn app.main:app --reload
```

**Sanity check**: open http://localhost:8000/docs — you should see a Swagger UI listing
`units`, `buildings`, `counterparties`, and the Foundation endpoints. You can create
records directly from this page to confirm the database round-trip works, before ever
touching the frontend.

---

## 4. Frontend setup

Open a **second terminal** (leave the backend running in the first):
```bash
cd frontend
npm install
npm run start
```

Open **http://localhost:4200**.

---

## 5. Using it

1. **General → Buildings**: Add new → create one.
2. **General → Landlords & Counterparties**: Add new → create one.
3. **General → Units**: Add new. The Building and Landlords fields are dropdowns
   populated from what you just created — or use the green **"+ Create new"** option
   inside either dropdown to create a building/landlord inline, without leaving the form.
4. Save the unit. It should appear in the grid with the building and landlord names shown
   (not raw IDs).
5. Go back to Buildings / Landlords & Counterparties — the **Units** column should now
   show a live count.
6. Deleting a building or landlord that's still referenced by a unit is blocked with an
   error — delete the unit first.

---

## 6. Inspecting the database directly

**pgAdmin** (usually installed alongside PostgreSQL): Servers → PostgreSQL → Databases →
`holiday_home_erp` → Schemas → public → Tables → right-click a table → **View/Edit Data →
All Rows**.

**psql**: open SQL Shell again, but connect to the app database this time (`Database:
holiday_home_erp`, `Username: erp`, `Password: erp`), then:
```sql
\dt                      -- list tables
SELECT * FROM unit;
```

### Why a row can exist in pgAdmin but not show in the app

**Delete in this app is a *soft* delete, by design** (records are archived, not destroyed
— this matters for an ERP's audit trail). Clicking delete doesn't run SQL `DELETE`; it
sets a `is_deleted = true` flag on the row. The app's API always filters `WHERE is_deleted
= false`, so a "deleted" record disappears from every screen — but a plain
`SELECT * FROM unit` in pgAdmin has no such filter and will still show it. To see only
what the app considers "live", add the filter yourself:
```sql
SELECT * FROM unit WHERE is_deleted = false;
```
This is expected behavior, not a bug.

---

## 7. Resetting your data

**Clear just Units/Buildings/Landlords data** (keeps Chart of Accounts etc.):
```sql
TRUNCATE TABLE unit_landlord, unit, building, counterparty;
```
Unit codes (`001`, `002`, ...) intentionally don't reset with this — they're tracked
separately and never reused, matching the "unit code is never reused" rule. If you want a
clean `001` again for testing:
```sql
DELETE FROM document_sequence WHERE doc_type = 'unit_code';
```

**Wipe everything** (including audit log, settings, chart of accounts):
```sql
TRUNCATE TABLE unit_landlord, unit, building, counterparty, account, audit_log, attachment, comment, document_sequence, entity, reference_list_item, setting;
```
Then re-seed so you're not left without the Chart of Accounts / reference lists:
```bash
cd backend
.venv/Scripts/python -m app.seed.run
```

**Manually deleting a row directly in pgAdmin**: foreign keys aren't cascading, so delete
in dependency order — `unit_landlord` rows referencing a unit before the unit itself,
and the unit before its building/landlord. Use the **Query Tool** (not the data grid) so
constraint-violation errors are visible; a grid edit that "doesn't stick" usually just
wasn't saved (there's a Save/floppy-disk button in the grid toolbar) or was silently
rejected by a foreign key. `TRUNCATE` (above) sidesteps this entirely since Postgres
resolves the order for you.

---

## 8. Troubleshooting

**`alembic: command not found` / `'alembic' is not recognized`** — your virtual
environment isn't activated. Either activate it (§3) or call it directly:
```bash
.venv/Scripts/alembic revision --autogenerate -m "..."     # Git Bash
.venv\Scripts\alembic.exe revision --autogenerate -m "..." # PowerShell / cmd
```

**Port 8000 or 4200 already in use** — you likely already have the backend/frontend
running in another terminal; that's fine, no need to start a second copy.

**CORS errors in the browser console** — the backend only allows `http://localhost:4200`
by default (see `backend/.env` → `CORS_ORIGINS`). If you're running the frontend on a
different port, add it there as a comma-separated list.

**Grids show "1 to ? of more" and never load data** — the frontend can't reach the
backend. Confirm `uvicorn` is actually running and http://localhost:8000/health returns
`{"status":"ok"}`.

---

## Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, PostgreSQL 16.
- **Frontend**: Angular 18 (standalone components), PrimeNG (layout/menu/forms/dialogs),
  ag-Grid Community (data grids).
- No auth/roles and no automated tests in v1 (deferred by explicit decision, plan §7) —
  every API endpoint is currently open.

## Repo layout

```
backend/    FastAPI app (app/core, models, schemas, services, routers, posting_rules, seed) + alembic/
frontend/   Angular workspace (src/app/core, shared, layout, features/*)
docs/       the build plan (pdf + generator script)
docker-compose.yml
```

## What's built vs. scaffolded

| Module | Backend | Frontend |
|---|---|---|
| Units, Buildings, Landlords & Counterparties | Full CRUD, real relationships enforced | Full grid + add/edit/delete, relationship dropdowns with inline "+ Create new" |
| Everything else in the sidebar | Not built yet | Real grid/form UI already wired to the planned REST endpoints — will work as soon as its backend exists |

## Next up

Same layered pattern (model → schema → service → router on the backend; the pattern is
already proven end-to-end) applied to the next module — tell me which one to build next.
