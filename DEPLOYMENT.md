# GOD’S EYE — manual free-tier deployment

**Status: prepared, not deployed.** This repository contains deployment configuration, but no Render service, Supabase project or live API has been provisioned or tested. Do not publish a guessed Render URL or database credential. Complete the provider steps below manually and verify the API before configuring the production frontend.

## Source inspection and deployment shape

- FastAPI entry point: `backend/main.py`, exported as `app`.
- Render working/root directory: `backend`.
- Render start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
- Render build command: `pip install -r requirements-api.txt`.
- Health endpoint: `/health`; dashboard endpoints include `/api/overview` and `/api/india-feeds`.
- `backend/db.py` defines persistent SQLAlchemy tables for `cameras`, `events`, and `camera_metrics`. Production forbids SQLite. The application creates missing tables at startup and applies its existing camera-column compatibility additions.
- The existing `frontend/next.config.mjs` reads the **server-side** environment variable `API_URL` and rewrites same-origin `/api/*` requests to that backend. Set `API_URL` in Vercel; do not use a `NEXT_PUBLIC_` variable for it.

## 1. Publish/connect the source repository

Push the reviewed project to the intended GitHub repository, preserving its existing history. Do not upload `.env`, passwords, API tokens, database dumps, or generated local data. The project `.gitignore` excludes environment files and local SQLite/evidence data; check the staged file list before pushing.

In Render, create a new Web Service from that repository and select the repository’s `render.yaml` Blueprint. Confirm the service uses the **Free** plan and that its root directory is `backend`. Do not enable a paid instance, persistent disk, or other paid add-on. The Blueprint installs only the lean API/database dependency set; the vision packages are deliberately excluded from this hosted service.

## 2. Create the Supabase Free database and obtain its Session pooler URL

1. Create a Supabase project on the **Free** plan in a region you choose.
2. In Supabase **Connect**, select the **Session pooler** connection string (not the direct database URI and not the transaction pooler). Use port `5432` and database `postgres`.
3. URL-encode any special characters in the database password. The application normalizes the URI to psycopg v3 and enforces `sslmode=require` in production. It also rejects production URLs that are not a Supabase Session Pooler host on port 5432.
4. In Render’s service environment settings, set `DATABASE_URL` to the full Session pooler URI. Enter it directly in Render’s secret/environment UI; do not put it in GitHub, this document, Vercel, or chat.

Render’s Blueprint sets `DB_POOL_SIZE=1` to keep the service’s Supabase connection use small. The camera registry and event/metric records are in PostgreSQL and survive Render restarts. Local uploads and local evidence images are disabled because Render Free has ephemeral disk; evidence image bytes are not made persistent by this setup.

## 3. Configure the Render service environment

The Blueprint includes these required settings:

| Variable | Value / action |
| --- | --- |
| `APP_ENV` | `production` (Blueprint) |
| `DATABASE_URL` | Supabase Session pooler URI; set directly in Render as a secret |
| `FRONTEND_ORIGINS` | `https://gods-eye-dashboard-tau.vercel.app` — the currently assigned domain listed for the GOD’S EYE Vercel project; confirm it remains the project domain after deployment. Do not use the unrelated `gods-eye-dashboard.vercel.app` hostname. |
| `ADMIN_API_TOKEN` | Generate a random secret of at least 32 characters and set it directly in Render; never commit it or add it to Vercel |
| `ENABLE_VIDEO_ANALYTICS` | `false` (keep off on Render Free) |
| `ENABLE_LOCAL_UPLOADS` | `false` |
| `STORE_LOCAL_EVIDENCE` | `false` |
| `STARTUP_CAMERAS` | `0` |
| `RETENTION_HOURS` | `720` (30 days for PostgreSQL event/metric rows) |

To generate an admin secret locally, run `python -c "import secrets; print(secrets.token_urlsafe(48))"` and enter the result directly into Render. The API refuses production startup if this token is missing or shorter than 32 characters. Keep it out of command histories that are synchronized/shared; preferably use a password manager to generate and transfer it securely.

Production CORS accepts only exact HTTPS origins. The Render Blueprint already names the Vercel project’s currently assigned origin above. If the Vercel project domain changes, update `FRONTEND_ORIGINS` to the exact new origin (scheme + host, no path or wildcard) and redeploy the backend. The Vercel project is currently not deployed and has SSO protection on non-custom-domain deployments; review its public-access/protection setting manually before expecting unauthenticated public visitors to reach the frontend.

## 4. Deploy and verify the backend before setting Vercel `API_URL`

Deploy the Render service, wait until the Render health check passes, and copy the **actual** HTTPS hostname Render assigns. It does not exist in this repository and must not be guessed. Verify:

```sh
curl -i https://<actual-render-host>/health
curl -i https://<actual-render-host>/api/overview
curl -i https://<actual-render-host>/api/india-feeds
```

Expected health response is HTTP 200 with `database: "postgresql"` and `video_analytics: "disabled"`. The other two endpoints should return HTTP 200 with current API payloads. A database connection failure should make `/health` return HTTP 503, not a misleading healthy result.

Verify that writes require the administrator bearer token: an unauthenticated write must return HTTP 401. For example, an unauthenticated `POST /api/cameras` must be rejected before any camera is created. Authenticated write-capable operations remain limited by the hosted profile; adding cameras for video inference, uploading local files and local settings updates are disabled/not durable on this deployment.

## 5. Configure the Vercel frontend

The exact variable is **`API_URL`**, read by `frontend/next.config.mjs`. In the GOD’S EYE Vercel project’s Production environment, set it to the actual Render HTTPS origin copied after deployment, for example the form `https://<actual-render-host>` (no guessed service slug). Do not set `NEXT_PUBLIC_API_URL`; no such variable is read by this project. Do not put `ADMIN_API_TOKEN` or `DATABASE_URL` in Vercel.

Redeploy the frontend after adding `API_URL` because Next.js needs the rewrite target in its project configuration/build environment. Confirm the production frontend uses the assigned project domain, then check `/operations` and `/chennai` and inspect browser network requests for successful `/api/overview` and `/api/india-feeds` responses.

When an authorized operator first performs an action requiring a write, the UI asks for the Render `ADMIN_API_TOKEN`. It keeps that token only in the current browser tab’s `sessionStorage` and sends it as an `Authorization: Bearer` header; it is not embedded in the JavaScript bundle or a durable credential store. Same-origin scripts can access it, so this is not equivalent to a full login system. A 401 clears the saved tab token. This is a shared operator secret, not per-user identity or audit logging. Limit who receives it and rotate it in Render if exposed. For multiple operators or stronger identity controls, integrate an actual login/identity provider before expanding write access.

## Computer-vision feasibility and service separation

The existing analytics implementation is real CPU ONNX/OpenCV inference. The local measured API process with its model loaded used about **284 MB RSS** in the inspected environment, before accounting for Render’s different runtime, and its benchmarked inference is CPU-intensive. Render Free offers only 0.1 CPU and 512 MB RAM, so it is not a sound target for continuous multi-camera inference or stable inference FPS. The hosted service is therefore explicitly **API + PostgreSQL only**, and its `requirements-api.txt` omits OpenCV, NumPy, ONNX Runtime and scikit-learn. `main.py` loads the CV stack only when analytics are enabled; enabling analytics on this lean service will fail clearly rather than silently fabricating values.

The full pipeline and model files remain in the repository and in `backend/requirements.txt` for local or separately provisioned inference. Continuous processing needs a separate worker with substantially more CPU (or a suitable GPU), memory headroom, reliable access to authorized video sources, and durable object storage if evidence images must persist. Size that worker from measured throughput for the selected model, resolution, number of feeds and target FPS; no performance number is promised for an untested hosted worker. Render Free also sleeps when idle and has ephemeral local storage, so it cannot provide uninterrupted processing or durable local files.

With inference off, people counts, vehicle counts and inference FPS remain unavailable unless actual fresh inference samples exist. The API still serves persistent camera registry/event data and existing informational routes; periodic still-image source checks are not video analytics.

## Deployment acceptance checklist

- [x] Source is published to the intended public GitHub repository; seven-commit history is preserved; no credential files or local database files were pushed.
- [ ] Supabase Free project exists; its Session pooler URL is entered only in Render.
- [ ] Render Free service deployed from `render.yaml`; `DATABASE_URL` and a random `ADMIN_API_TOKEN` are set as environment secrets.
- [ ] `/health`, `/api/overview`, and `/api/india-feeds` pass against the deployed service.
- [ ] An unauthenticated write returns 401; authorized UI write requests carry the bearer token.
- [ ] The assigned Vercel origin is exact in `FRONTEND_ORIGINS` and CORS preflight is verified.
- [ ] Vercel Production `API_URL` is the exact Render HTTPS origin; frontend is redeployed and its API requests pass.
- [ ] Inference remains disabled on Render Free; no unverified live analytics are claimed.

**Until these checks are completed, deployment remains incomplete and no public API URL should be published as confirmed.**
