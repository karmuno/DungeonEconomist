# Sentry Error Tracking

Optional. With no DSN configured, both SDKs stay inert and the app runs normally.

VentureKeep reports errors from two places, so it needs **two Sentry projects** and **two
DSNs** — one for the Python backend, one for the Vue frontend.

## What is reported

| | |
| :--- | :--- |
| Backend | Uncaught exceptions from FastAPI |
| Frontend | Uncaught errors, Vue render and lifecycle errors, and failed API calls — 5xx responses and network failures |
| Every event | Tagged with the build string (`release`) and the environment |

Performance tracing, session replay and source-map upload are not enabled. Production
stack traces name minified bundle lines; Vue component names and breadcrumbs still come
through.

## 1. Create the projects

In Sentry, create two projects:

| Project | Platform | Gives you |
| :--- | :--- | :--- |
| Backend | **FastAPI** (Python) | `SENTRY_DSN` |
| Frontend | **Vue** | `VITE_SENTRY_DSN` |

Copy both DSNs. Keep them straight — they are not interchangeable.

## 2. Configure the backend

Two variables in the backend env file:

```
SENTRY_DSN=https://your-backend-key@o00000.ingest.us.sentry.io/00000
APP_ENV=production
```

`APP_ENV` sets the environment name Sentry groups by. Use `development` locally and
`production` on the server. If omitted it defaults to `development`.

| Environment | File |
| :--- | :--- |
| Local development | `.env` at the repo root |
| Production | `~/venturekeep/.env` |

**Do not quote the values.** Docker's `--env-file` keeps quote characters as part of the
value, which produces a malformed DSN that Sentry silently rejects.

## 3. Configure the frontend

One variable in the frontend env file:

```
VITE_SENTRY_DSN=https://your-frontend-key@o00000.ingest.us.sentry.io/00000
```

| Environment | File |
| :--- | :--- |
| Local development | `frontend/.env` |
| Production | `~/venturekeep/frontend/.env` |

Two rules for this one:

- **The `VITE_` prefix is required.** Vite only exposes prefixed variables to browser code.
  Without it, nothing is reported and nothing warns you.
- **It must exist before the frontend is built.** Vite compiles the value into the JavaScript
  bundle, so on the server the file must be in place before `docker build`. Setting it at run
  time has no effect.

**The frontend environment needs no variable.** Vite sets it from the build mode —
`development` under `npm run dev`, `production` in a build — and the app reports that
automatically. `APP_ENV` is backend-only and does nothing in `frontend/.env`.

## 4. Verify

Backend, on the server:

```bash
docker exec venturekeep-app printenv SENTRY_DSN APP_ENV
```

Frontend: open the deployed page, view source, and search the JavaScript for `ingest`. If the
DSN is not in the bundle, the build did not see `frontend/.env` — rebuild after creating it.

Then trigger an error and confirm it arrives in the right project with the expected
environment.

## 5. Recommended Sentry settings

The frontend DSN ships inside the JavaScript bundle and is visible to anyone who views the
page. This is expected — a DSN only permits submitting events, not reading them — but it does
let a stranger spend your quota. In the **frontend** project:

- **Inbound Filters → Allowed Domains**: set to your domain, so only events from your site are
  accepted.
- Leave **spike protection** enabled.

Treat the backend DSN as private. It is never sent to a browser, so keep it out of anything
public.

## Variable reference

| Variable | File | Read at |
| :--- | :--- | :--- |
| `SENTRY_DSN` | `.env` (local) · `~/venturekeep/.env` (production) | Run time |
| `APP_ENV` | `.env` (local) · `~/venturekeep/.env` (production) | Run time |
| `VITE_SENTRY_DSN` | `frontend/.env` (local) · `~/venturekeep/frontend/.env` (production) | **Build time** |

All of these files are gitignored. They do not exist on a fresh clone and `git pull` will not
remove them — recreate them when setting up a new machine or server.
