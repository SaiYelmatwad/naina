# Signalwork — AI Career Intelligence

A full-stack app that scores a job posting against your real skill profile:
what matches, what's missing, and why — backed by a real Postgres database,
not a mock.

Built as a demonstration of production backend practices (migrations,
indexes, auth, pagination, structured logging, tested error handling) and a
working full-stack integration — a project to point to in an interview,
not just a mock.

---

## 1. Architecture

```
┌─────────────┐      HTTP/JSON       ┌──────────────┐      SQL       ┌────────────┐
│   React SPA │ ───────────────────► │  FastAPI     │ ─────────────► │ PostgreSQL │
│ (Vite, TS)  │ ◄─────────────────── │  (JWT auth)  │ ◄───────────── │            │
└─────────────┘                      └──────────────┘                └────────────┘
    nginx (prod)                      uvicorn/gunicorn                Alembic-managed
    reverse-proxies                   app/matching/ scores             schema, indexed
    /api → backend                    role text vs. skills             on (owner_id, created_at)
```

- **Frontend**: React 19 + TypeScript + Vite 8 + Tailwind v4. Talks to the API
  only through a typed client (`src/api/client.ts`) — no component calls
  `fetch` directly except the paginated Applications list, which needs
  per-page query params the shared client doesn't abstract yet (see
  Trade-offs).
- **Backend**: FastAPI, organized by concern, not by "everything in
  main.py":
  - `app/routers/` — HTTP layer (one file per resource)
  - `app/matching/` — the scoring engine, decoupled from FastAPI entirely
    (it's plain Python — could run in a batch job with zero changes)
  - `app/core/` — cross-cutting concerns (logging middleware, pagination)
  - `app/models.py` / `schemas.py` — DB layer vs. wire layer kept separate
    on purpose, so a schema change doesn't silently become an API change
- **Database**: PostgreSQL 16, schema owned by Alembic migrations (not
  `create_all()` — see Trade-offs for why that distinction matters).

## 2. Data flow: a scan, end to end

1. Client sends `POST /scan` with `role_text` and a bearer JWT.
2. `deps.get_current_user` decodes the JWT, loads the user, or the request
   dies at `401` before touching business logic.
3. `routers/scan.py` loads the user's `Skill` rows (already scoped to
   `owner_id` — see §5) and hands `(role_text, skills)` to
   `matching/scorer.py`.
4. `scorer.py` asks `matching/embeddings.py` for a similarity between the
   role text and each skill name, splits results into `matched` (skill
   present in profile, level ≥ 0.55) and `gaps` (present, level < 0.55),
   and computes a weighted score from coverage, matched-skill strength, and
   role relevance.
5. The scan is persisted to `scans` (for `/scan/history`) before the
   response is returned — a user can always see what they scanned, even if
   they never save it as an application.
6. Client renders the score, gauge, matched/gap lists, and offers to save
   it as a tracked `Application`.

## 3. The matching algorithm — and its honest limits

`app/matching/embeddings.py` defines an `EmbeddingProvider` interface with
one real implementation, `TfidfEmbeddingProvider`:

- **TF-IDF cosine similarity** (scikit-learn) between the role text and each
  skill name — a real vector-similarity technique, not a keyword count.
- **+ a lexical boost**: a short skill name ("python") gets diluted to
  near-zero by pure cosine similarity against a long sentence, because the
  sentence's other words dominate the vector. Production hybrid-search
  systems handle this by blending a lexical (exact-term) signal with the
  vector signal — this does the same, with a word-boundary regex check that
  floors the score at 0.65 on a literal mention.
- This is **fully local — no API key, no network call, no downloaded
  model**. It runs in the request path with no added latency.

**What this is not**: true semantic understanding. It won't know that
"led a team" implies "leadership" unless "leadership" or a near-synonym
literally appears. `LLMEmbeddingProvider` in the same file is a real,
documented extension point — swap `get_embedding_provider()` to return it
once you wire in an embeddings API key, and nothing in `scorer.py` changes,
because both providers share the same interface. This part isn't faked by
hard-coding what an LLM call would return; the stub raises
`NotImplementedError` until a key is actually wired in, which is more
honest than shipping a canned response and calling it "AI-powered."

## 4. API reference

All endpoints except `/health`, `/auth/register`, `/auth/login` require
`Authorization: Bearer <token>`.

| Method | Path                            | Description                                    |
|--------|----------------------------------|-------------------------------------------------|
| GET    | `/health`                       | Liveness — process is up                        |
| GET    | `/health/ready`                 | Readiness — DB reachable (`SELECT 1`)            |
| POST   | `/auth/register`                | Create account                                   |
| POST   | `/auth/login`                   | OAuth2 password flow → JWT                       |
| GET    | `/profile/me`                   | Current user                                     |
| GET    | `/profile/skills`                | List skills                                      |
| POST   | `/profile/skills`                | Add a skill (unique per user+name)               |
| DELETE | `/profile/skills/{id}`           | Delete a skill (owner-only, else 404)            |
| POST   | `/scan`                          | Score `role_text` against the caller's skills    |
| GET    | `/scan/history?page&page_size`   | Paginated scan history                           |
| GET    | `/applications?page&page_size`   | Paginated application list                       |
| POST   | `/applications`                  | Track an application                             |
| PATCH  | `/applications/{id}`             | Update status (owner-only, else 404)             |
| DELETE | `/applications/{id}`             | Remove (owner-only, else 404)                    |

Interactive docs at `/docs` (Swagger UI, auto-generated by FastAPI).

## 5. Security & validation

- **Passwords**: bcrypt via passlib. Max length capped at 72 bytes in the
  Pydantic schema because bcrypt silently truncates beyond that — an
  unbounded max gives a false sense of strength.
- **JWT**: HS256, 24h expiry, `sub` = email, verified on every protected
  route via `deps.get_current_user`.
- **Authorization, not just authentication**: every query is scoped to
  `owner_id == current_user.id` at the DB layer. Accessing or modifying
  another user's skill/application returns a plain `404`, not `403` — this
  is deliberate: a `403` confirms the resource exists and isn't yours,
  which is an enumeration leak. Covered by `tests/test_authorization.py`
  (cross-user read, delete, and patch attempts).
- **Input validation**: length bounds on every string field (a role-text
  scan is capped at 8000 chars — protects the TF-IDF step from someone
  pasting a full PDF and spiking CPU), skill level constrained to `[0,1]`
  at both the Pydantic layer and a Postgres `CHECK` constraint (defense in
  depth — the DB doesn't trust the API to be the only writer forever),
  application `status` restricted to a fixed enum at both layers.
- **Error handling**: a duplicate skill name hits a Postgres `UNIQUE`
  constraint, caught by a global `IntegrityError` handler and turned into a
  clean `409`, not a raw stack trace. Verified live, not just unit-tested:
  `curl`-ing a duplicate skill returns `409` end-to-end.

## 6. Database schema, migrations, indexes

Schema is owned by **Alembic**, not `Base.metadata.create_all()`. This
matters for a real reason: `create_all()` can't express an `ALTER TABLE`,
so the moment you need to add a column to a table with existing data, you
have no story for it. Alembic's autogenerate diffed the real schema against
the models and produced the initial migration in this repo
(`backend/alembic/versions/`) — it wasn't hand-written from memory.

Indexes (all present in the generated migration, verified against a live
Postgres via `psql \d`):

- `users.email` — unique + indexed (login lookup)
- `skills(owner_id, name)` — unique constraint (no duplicate skills per
  user) + indexed on `owner_id` (every skills query filters by it)
- `scans(owner_id, created_at)` — composite index; `/scan/history` always
  filters by owner and sorts by time, so this is the exact access pattern
- `applications(owner_id, created_at)` — same reasoning

`ON DELETE CASCADE` on all owner foreign keys, so deleting a user cleans up
their skills/scans/applications at the DB level, not via application code
that's easy to forget to update.

## 7. Pagination & performance

- `/scan/history` and `/applications` take `page` / `page_size` query
  params (default 20, max 100, enforced server-side so a client can't
  request an unbounded number of rows in one call) and return
  `{items, meta: {total, page, page_size, has_next}}`.
- `pool_pre_ping=True` on the SQLAlchemy engine — avoids serving a request
  on a connection Postgres already dropped (idle timeout, restart), which
  is a real class of intermittent 500s in long-running services.
- Frontend: route-based code splitting (`React.lazy` + `Suspense`) for
  Dashboard/Scanner/Applications, specifically because Recharts pushed the
  main JS bundle over Vite's 500kB warning threshold. Splitting it out
  dropped the `/login` bundle from 561kB to ~267kB gzipped — verified by
  actually running the build before and after, not assumed.

## 8. Testing

**22 tests, all passing against a real PostgreSQL database** (not SQLite —
the test suite intentionally runs against the same engine as production, so
Postgres-specific behavior like `CHECK`/`UNIQUE` constraints and `ON DELETE
CASCADE` is actually exercised):

- `test_auth.py` — register, login, duplicate email, wrong password,
  unauthenticated access to a protected route
- `test_matching.py` — unit tests on the scoring engine directly (no HTTP),
  including that TF-IDF similarity behaves sanely on identical vs.
  unrelated text
- `test_scan.py` — scan scoring through the API, pagination behavior
  (`has_next` correctness across pages), oversized/empty input rejection
- `test_authorization.py` — edge cases, not just happy paths: a second
  user cannot read, delete, or patch a first user's data; invalid email
  and short passwords are rejected at validation; a duplicate skill name
  returns `409` not `500`; an invalid application status is rejected;
  garbage JWTs are rejected; deleting a user cascades to their skills at
  the DB level

Run them: `cd backend && pytest tests/ -v`

## 9. Setup

### Option A — Docker Compose (recommended)

```bash
cp .env.example .env   # optional, only if you want to override JWT_SECRET
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000/docs
- Postgres: localhost:5432 (user/pass `postgres`/`postgres`, db `signalwork`)

The backend container runs `alembic upgrade head` on startup, before
`uvicorn` starts (see `backend/docker-entrypoint.sh`) — the schema is never
out of sync with the code that's running.

### Option B — run locally without Docker

```bash
# Postgres running locally, then:
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# separate terminal
cd frontend
npm install
npm run dev   # http://localhost:5173, proxies /api -> localhost:8000
```

## 10. Trade-offs and known gaps (stated plainly, not hidden)

- **TF-IDF, not a neural embedding model.** Documented in §3. The
  extension point is real and unused-until-wired, not faked.
- **`oxlint` reports 1 warning, 0 errors** on the frontend:
  `react-refresh/only-export-components` on `AuthContext.tsx`, because it
  exports both the `AuthProvider` component and the `useAuth` hook from the
  same file. This is a Fast Refresh nicety, not a correctness issue —
  fixing it means splitting a 90-line file into two for marginal benefit,
  so it's left as-is.
- **No refresh tokens** — JWT is a flat 24h expiry. Fine for a demo; a
  production version would want short-lived access tokens + refresh
  rotation.
- **CORS is restricted to `localhost:5173`/`3000` in dev**, but there's no
  per-environment config wired up yet for a real deployed frontend origin.
- **No rate limiting.** Deliberately left out rather than bolted on with a
  library that couldn't be verified end-to-end here — the brief said not
  to add technology for its own sake, and untested rate limiting is worse
  than none.

## 11. What was actually verified vs. not, in this environment

**Verified by actually running it:**
- `pytest tests/ -v` → 22/22 passing, against a real PostgreSQL 16 server
  installed and running in the build environment (not SQLite, not mocked)
- `alembic upgrade head` → applied to a live Postgres DB; schema inspected
  afterward via `psql \dt` / `\d skills` and confirmed indexes/constraints
  exist as designed
- Live end-to-end smoke test via `curl`: register → login → add skill →
  scan → real score returned → pagination on an empty list → duplicate
  skill → `409` (not a crash)
- `ruff check` → clean, 0 issues
- `npm run build` → succeeds; bundle sizes measured before/after code
  splitting
- `npm run lint` (oxlint) → 0 errors, 1 documented warning
- `docker-compose.yml` and both `Dockerfile`s → validated as syntactically
  correct YAML, and every file path they reference was confirmed to exist.
  The backend entrypoint's actual logic (DB-readiness check + `alembic
  upgrade head`) was run directly against the real Postgres instance to
  confirm it works, not just read for correctness.

**Not verified — this sandbox's network allowlist blocks Docker Hub:**
- `docker compose up --build` was attempted, not just written and assumed.
  Docker itself installs and runs fine here (`docker version`, `docker
  compose config` all succeed), and `docker compose config -q` confirms the
  compose file parses and resolves correctly. But `docker build` on the
  backend image fails at `FROM python:3.12-slim` with a `403 Forbidden`
  from `registry-1.docker.io` — this environment's outbound network
  allowlist doesn't include Docker Hub, so no image (not even a base image)
  can be pulled. This is an environment restriction, not a bug in the
  Dockerfiles or compose file — but it does mean the containers actually
  starting together, healthchecking correctly, and talking to each other
  has **not** been proven end-to-end. Everything each container *runs*
  (migrations, uvicorn, the entrypoint script's DB-wait logic, the nginx
  config's `/api` proxy path) was verified directly against the real
  Postgres instance outside a container instead. Run `docker compose up
  --build` once on a machine with normal internet access before relying on
  it — that step is genuinely untested.
- GitHub Actions CI (`.github/workflows/ci.yml`) was authored and YAML-
  validated, and every command in it (`ruff check`, `alembic upgrade
  head`, `pytest`, `npm run lint`, `npm run build`) was run directly in
  this environment and confirmed to work — but the workflow file itself was
  never executed on GitHub's runners, since there's no way to trigger a
  real Actions run from here. Push it and watch the first run before
  treating it as proven.
