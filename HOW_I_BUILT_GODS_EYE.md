# HOW I BUILT GOD'S EYE – DEVELOPMENT JOURNEY

This document describes the current GOD'S EYE implementation and a reproducible local workflow. It distinguishes implemented functionality from plans and deployment work that is still pending.

## STEP 1 – Project Concept and Planning

The project explores combining computer vision, video analytics, geographic context and camera-source information in one public-safety-oriented dashboard. Its intended users include developers, students and operators reviewing source availability and video-derived events. The key product constraint is that AI outputs are assistance for human review: the application does not identify people, classify criminal intent or contact authorities.

The India-facing source model is deliberately honest. Two Chennai records are third-party **periodic still-image** sources, not continuous public CCTV and not YOLO inputs. The Indian traffic clip is a separate **prerecorded demonstration** whose exact city is unverified.

## STEP 2 – Development Environment

### Tools and languages

- Node.js 20+ and npm, with the committed `frontend/package-lock.json` for repeatable frontend installation.
- Python 3.13 in the verified workspace; the backend requirements declare FastAPI, SQLAlchemy, OpenCV, ONNX Runtime, NumPy, Pydantic and supporting packages.
- TypeScript/TSX, JavaScript modules, CSS, Python and SQLAlchemy models.
- Git for version control. The supplied workspace has an existing local `main` history with two meaningful commits. No remote is configured; preserve both commits and add the authenticated GitHub remote only after confirming the account repository.

### Project structure

```text
.
├── PROJECT_OVERVIEW.md
├── HOW_I_BUILT_GODS_EYE.md
├── README.md
├── PROJECT_STATUS.md
├── frontend/
│   ├── app/                 # Next.js pages, dashboard, map, video hero, styles
│   ├── public/data/         # Bundled state/UT GeoJSON
│   ├── package.json
│   ├── package-lock.json
│   ├── next.config.mjs      # Same-origin /api rewrite via API_URL
│   └── vercel.json          # Next.js production build settings
├── backend/
│   ├── main.py              # FastAPI routes and async source workers
│   ├── cv_engine.py         # ONNX detector, IoU tracking and event cues
│   ├── db.py                # SQLAlchemy models and database setup
│   ├── models/              # ONNX detector and optional model files
│   ├── tests/               # Backend and data validation tests
│   └── requirements.txt
├── data/media/              # Attributed test clips and Indian demo MP4
├── docs/                    # Architecture, evaluation, source and provenance notes
└── scripts/                 # Reproducible public map-data generation
```

Runtime databases, evidence snapshots, uploads, local environment files, node modules, caches and build outputs are excluded by `.gitignore`.

## STEP 3 – Frontend Development

`frontend/app/page.tsx` redirects to the video-first dashboard, implemented in `frontend/app/operations/page.tsx`; both `/` and `/operations` show the Overview, Live Monitoring, Incidents, Analytics, Cameras and System Settings navigation. The Chennai source-availability information page is maintained separately at `/chennai`. The top bar, camera station viewer, KPI tiles, event list and source-management panels are React components. Recharts renders actual retained analytics; the UI avoids replacing missing measurements with invented values.

`frontend/app/globals.css` defines the dark dashboard surface, cyan/turquoise accents, type hierarchy, responsive breakpoints and restrained transitions. The layout uses flexible grids, wraps map controls, retains mobile bottom navigation and includes reduced-motion handling. The top-left lockup retains the product name and **PUBLIC SAFETY INTELLIGENCE**, with **MADE BY JOE V KADAVAN** beneath it; on tablet and phone the equivalent lockup appears in the top bar. The short first-load intro repeats that lockup at its upper-left so authorship is visible immediately.

## STEP 4 – GOD'S EYE 3D Branding

The eye mark is the existing inline SVG/CSS implementation in `frontend/app/EyeLogo.tsx`. It layers an eye contour, iris, pupil and glint, then uses CSS perspective, a slow iris drift and a brief, irregular blink. No WebGL or external 3D package is used for the logo. `prefers-reduced-motion` disables the relevant animations. The final branding work leaves the eye illustration itself intact.

## STEP 5 – Video Integration

The Overview begins with `frontend/app/DemoHero.tsx`, using the existing bundled `data/media/indian-urban-traffic-pexels-5009674.mp4`. The backend exposes a demo-ID-restricted `GET /api/cameras/{camera_id}/video`; Starlette `FileResponse` supports byte-range requests so a browser can seek the MP4 through Next.js's same-origin `/api/*` rewrite. The HTML video uses `autoPlay`, `muted`, `loop` and `playsInline`; controls provide play/pause, restart, mute/volume and fullscreen. The 16:9 source is contained rather than stretched, with responsive overlays and a professional buffering/error state.

The backend inference worker decodes the same prerecorded source independently. `GET /api/cameras/{camera_id}/telemetry` returns current YOLO detections, metrics and worker media position. The hero polls that endpoint; it seeks when media drift exceeds the configured threshold and only draws bounding boxes when the video and worker positions meet the sync tolerance. While they do not align, boxes are hidden and the status reports syncing. This is a prerecorded demo, never live CCTV. The separate fullscreen camera station remains a synchronized processed-frame viewer.

## STEP 6 – AI Video Analytics

The default model is YOLOv8n exported to ONNX and executed by ONNX Runtime's CPU provider. OpenCV reads a video/file frame, letterboxes it to the configured input size, runs inference and applies confidence filtering and class-aware non-maximum suppression. COCO class 0 is `person`; selected vehicle classes are 2 (`car`), 3 (`motorcycle`), 5 (`bus`) and 7 (`truck`). Detections carry coordinates, class, confidence and an ephemeral track ID.

A small class-aware IoU tracker associates boxes between nearby frames. Track IDs are temporary and local to a camera worker; they are not personal identities and are not linked across cameras. The analyzer computes people/vehicle counts, maximum observed people count, pixel-normalised people density, crowd level, a newly appearing vehicle-track flow proxy, inference latency and rolling FPS. For the Overview's traffic panel, it also computes the clipped union area of detected vehicle boxes as a frame-occupancy percentage (avoiding overlap double-counting) and assigns transparent LOW / MODERATE / HIGH / VERY_HIGH bands. It estimates movement from recent tracked vehicle-center displacement normalized to frame diagonal and time; without enough observed track history, flow is unknown rather than stationary. These are visual proxies—not calibrated roadway capacity or physical vehicle speed. Bounding boxes and confidence scores are returned to the frontend and drawn over video/processed frames.

The code also has temporal cues for possible falls, prolonged stationary non-person/non-vehicle objects, rapid image-plane motion and sudden crowd increases. These are unvalidated heuristics—not trained action recognition, intent inference or reliable incident classification. Alerts require a human to review them. Chennai image-refresh feeds are excluded from computer vision.

```text
Prerecorded/local/authorized video
        │
        ▼
OpenCV camera_worker ──► YOLOv8n ONNX inference
        │                         │
        │                         ├── boxes, COCO labels, confidence
        │                         └── temporary camera-local IoU track IDs
        ▼
CameraState metrics + heuristic event cues
        ├── hub.latest / synchronized frame APIs ──► hero and station viewer
        ├── SQLAlchemy metric/event records ───────► analytics and event pages
        └── temporary evidence image ──────────────► human review workflow

Periodic still-image registry sources ─────────────► source metadata only
                                                   (no YOLO inference)
```

## STEP 7 – Camera Registry

SQLAlchemy `Camera` records are served by FastAPI and exposed in `/api/overview`. The frontend uses registry-provided name, feed type, state/city, numeric coordinates, status, last check, last successful image refresh and attribution. Coordinates are not derived from city names or map click points.

The verified Chennai entries use the database values: Choolaimedu High Road at **13.06372, 80.23031** and Tiruvottiyur at **13.19230, 80.31570**. They are third-party image-refresh sources; periodic availability and image timestamps are shown as such. The station viewer displays source details and attribution and invokes the existing viewer for the selected source. The prerecorded demo has no verified city coordinates and is not plotted as a camera.

Local video uploads and authorized local/RTSP sources are separate registry functionality. Never commit source credentials or add feeds without permission.

## STEP 8 – Interactive India Map

`frontend/app/IndiaMap.tsx` lazily imports MapLibre when the map approaches the viewport and preserves its map instance when registry data updates. The base styles are OpenFreeMap Dark (default), Liberty, Positron and Bright, using OpenMapTiles/OpenStreetMap-derived vector tiles. MapLibre provides pan, zoom, compass/rotation, tilt, attribution and the fullscreen map container. City navigation is for map browsing only; those destinations do not create camera locations.

A locally bundled GeoJSON contains 36 simplified geoBoundaries gbOpen India ADM1 polygons; its generator is `scripts/build_india_admin1.py`. It is attributed CC BY 4.0 and is a visual reference—not a legal/cadastral boundary determination. MapLibre camera layers are built from the actual filtered registry coordinates, with turquoise availability markers, labels and click details. The marker panel shows status and recorded last-image time and its **Open Camera** button opens the existing camera viewer.

At high city zoom, the optional 3D toggle pitches the map and enables a fill-extrusion layer over mapped `building` features in the OpenMapTiles vector source. It uses height attributes where available; unmapped footprints cannot be extruded. No satellite layer is configured by default. It can appear only if an operator provides a properly licensed style URL using `NEXT_PUBLIC_SATELLITE_STYLE_URL`; that browser-facing value is public and must not contain server secrets. No Google Maps API, paid tile plan or satellite subscription is used by default.

OpenFreeMap's published public terms, as reviewed for this project, state there is no map-view/request quota or charge for the public instance, permit commercial use and require attribution. The service is provided as-is with no SLA and can change/discontinue. Its offline-download limits (3,000 tiles / 50 MB / four parallel requests per user-started download) do not apply to this app, which has no offline bulk downloader. See `docs/geospatial-map.md` for source and license details.

## STEP 9 – Alerts and the Incident Register

The backend creates persisted event records from configured detector cues, camera lifecycle conditions and temporal/count heuristics. Events include an ID, camera, category, timestamp, model-derived confidence where supplied, description, severity, verification state and optional short-lived evidence URL. The Incidents page allows operators to acknowledge, verify or dismiss events; the Overview retains its actionable alerts-requiring-review list. The former Overview Recent Events panel has been removed as a targeted replacement with traffic-flow intelligence. Demo playback lifecycle is not a real public-safety alert. Historical events remain subject to configured retention.

Severity labels are triage/UI categories, not a calibrated risk probability. Detector confidence is not alert validity. Human verification is required, no emergency service is contacted automatically, and no claim of measured event accuracy is made.

## STEP 10 – Dashboard Analytics

KPI cards use `/api/overview`, current worker metrics and runtime system information. Recharts activity views and analytics page visualisations use persisted `CameraMetric` history and actual event/category records returned by `/api/analytics`. The Overview Traffic Flow & Congestion Intelligence component reads selected-camera samples from that same retained history; selectable 5-, 15- and 30-minute trends require at least two actual timestamped samples, with no synthetic points. Historical timestamps are normalized to UTC for consistent browser filtering. Camera comparison is restricted to registered video sources, and source freshness is shown separately from endpoint availability. Insights compare observed samples and current tracked motion only; they do not invent incidents or forecasts. Sampling and retention determine what history is available; the UI notes those limits. Missing measurements display as unavailable rather than fabricated zeroes. Density uses unioned vehicle-box frame coverage (not capacity), and tracked flow uses image-plane displacement (not calibrated speed). Prerecorded feeds are explicitly identified; still images do not contribute AI counts.

## STEP 11 – Testing and Refinement

The project includes pytest tests for inference/tracking behavior, camera lifecycle and API functions, event history, map GeoJSON integrity and video route restrictions. For this delivery pass:

- `cd frontend && npm run build` completed successfully on the current source state.
- `cd backend && pytest -q` passed **34 tests**, including Session pooler validation, API-only imports without CV libraries, write-route bearer protection, CORS validation and no-inference safeguards.
- A production-build Chromium smoke test visited `/`, `/operations`, and `/chennai`; all returned successfully with no page errors or hydration console errors. At 390 px, both dashboard and Chennai pages had no horizontal overflow. The dashboard video element loaded, the Chennai page rendered two source cards, and the production API smoke returned HTTP 200 for `/health`, `/api/overview`, and `/api/india-feeds` in local configuration.
- No Render service or Supabase project/database exists yet; the app has not been tested against a live hosted database.

For future changes, run `npm ci`, `npm run build`, then `python3 -m pytest -q backend/tests`. Smoke-test `/`, `/api/overview`, `/data/india_admin1.geojson` and the map-style/MP4 requests from a browser with an approved backend URL.

## STEP 12 – GitHub Version Control

The requested URL `https://github.com/Joevkadavan/gods-eye-dashboard` returned HTTP 404 to an unauthenticated GitHub API lookup. That may mean it does not exist or that it is private; a private repository cannot be ruled out without authentication. The workspace has a local `main` branch with six truthful commits, including the original history, final dashboard update, launch record and Render/Supabase preparation; these commits must be preserved. No Git remote or GitHub CLI is configured, and the GitHub connector is not available in this session, so no remote repository has been created or overwritten and no push is claimed. An authenticated GitHub connection is required before verifying a private repository, creating it if absent, or pushing source.

After authenticating GitHub with an approved mechanism, first verify the repository in the account. The GitHub web interface can create a public repository at `https://github.com/new` with the name `gods-eye-dashboard`. If GitHub CLI is installed and authenticated, check first with `gh repo view Joevkadavan/gods-eye-dashboard`. If absent, an empty repository can be created and published with `gh repo create Joevkadavan/gods-eye-dashboard --public --source . --remote origin --push` after the local source has a real commit. If present, clone/fetch it first and preserve its history. Then, from the project root:

```bash
# If starting from the empty remote, initialize once:
git init -b main
git add .
git status                 # inspect staged files; verify no .env/database/cache
# Use the authenticated developer identity configured on your machine:
git commit -m "Prepare GOD'S EYE dashboard source and launch documentation"
git remote add origin https://github.com/Joevkadavan/gods-eye-dashboard.git
git push -u origin main
```

If a remote already has commits, clone that remote and copy the final source into it, then commit and push normally; do not force-push or synthesize earlier commits. For subsequent updates use `git add`, `git commit -m "Describe the change"` and `git push`. The repo URL is [Joevkadavan/gods-eye-dashboard](https://github.com/Joevkadavan/gods-eye-dashboard).

## STEP 13 – Vercel and Render Deployment (manual steps pending)

Vercel has a `gods-eye-dashboard` project configured with the Next.js app rooted at `frontend`, but it is not connected to a repository and has no deployment. The current Vercel project domain listing returns `gods-eye-dashboard-tau.vercel.app`; use `https://gods-eye-dashboard-tau.vercel.app` as the current CORS origin and re-check after deployment. Do not use `gods-eye-dashboard.vercel.app`, which serves unrelated content, and do not alter the unrelated `bealwaysjoe` project. The project currently has SSO protection for non-custom-domain deployments; verify public-access policy before announcing a public site.

The exact frontend backend target variable is server-side `API_URL`, which `frontend/next.config.mjs` reads for same-origin `/api/*` rewrites. After a Render service is created, enter its actual HTTPS origin in Vercel Production `API_URL` and redeploy. The origin cannot be supplied until Render assigns it.

The root `render.yaml` configures Render Free with `rootDir: backend`, build command `pip install -r requirements-api.txt`, start command `uvicorn main:app --host 0.0.0.0 --port $PORT`, and `/health`. The lean API requirements intentionally omit OpenCV, NumPy, ONNX Runtime and scikit-learn. The existing vision stack remains available via the full `backend/requirements.txt` for local or separately provisioned inference. The Render environment asks for `DATABASE_URL` and `ADMIN_API_TOKEN` as unsynced secrets; the Blueprint sets `FRONTEND_ORIGINS` to the current exact Vercel project origin.

Create the Supabase Free PostgreSQL project manually and use its Session pooler URI (host under `.pooler.supabase.com`, port 5432, database `postgres`) only as Render's secret `DATABASE_URL`. Production requires TLS, rejects SQLite and enforces the Session pooler host/port. SQLAlchemy models persist camera registry, event and metric rows. The service turns video inference, local uploads and local evidence writes off. A 30-day retention policy applies to event and metric rows.

Production requires an `ADMIN_API_TOKEN` random secret of at least 32 characters. All HTTP write endpoints reject requests without its bearer token. The web UI prompts the operator for this shared token at first write and stores it only in that tab's session storage; it is not embedded in frontend code. This is shared-secret access, not per-user identity or audit history.

Render Free's 0.1 CPU / 512 MB service is not suitable for continuous multi-camera ONNX inference. The hosted process is API + PostgreSQL only; real analytics require a separate appropriately sized CPU/GPU worker, authorized sources, and durable object storage if evidence files must persist. The API returns no synthetic counts or FPS while inference is disabled. Render Free also sleeps and has ephemeral storage. No Render URL exists yet. No Supabase project was found in the connected account listing; no Render service was created; no GitHub remote is configured or pushed. The live deployment procedure, environment names and acceptance checks are documented in [`DEPLOYMENT.md`](DEPLOYMENT.md).

## STEP 14 – Running the Project Locally

From a clean clone, install Node.js 20+ and Python 3.13, then open two terminals from the repository root.

```bash
git clone https://github.com/Joevkadavan/gods-eye-dashboard.git
cd gods-eye-dashboard
python3 -m venv .venv
source .venv/bin/activate                 # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
cp backend/.env.example backend/.env       # edit only local, untracked values
```

Terminal 1 — FastAPI API and OpenCV workers:

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Terminal 2 — Next.js frontend (from the repository root):

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:3000`; optional API docs are at `http://localhost:8000/docs`. The Next.js rewrite defaults to local `http://127.0.0.1:8000`; production must set `API_URL` explicitly.

Production frontend build and local production server:

```bash
cd frontend
npm run build
npm run start
```

For the optional Docker Compose setup, copy `.env.example` to an untracked `.env`, replace its local placeholder values, then run `docker compose up --build`. Never commit local `.env` files, database data, upload/evidence data or API credentials.

## STEP 15 – Future Development

Potential future work (not represented as shipped functionality) includes authenticated operator roles, secure deployment hardening, a documented backend hosting strategy, browser-based responsive/accessibility QA, offline-capable mapped data within provider terms, versioned boundary updates, camera health audit history and a labelled, independently evaluated dataset for validating event cues. Satellite imagery would require explicit selection of a properly licensed provider and a review of its costs and terms. Any future live-camera integration requires authorization and must not turn periodic still-image sources into claims of continuous video.

## Final Author Information

**MADE BY JOE V KADAVAN**

GitHub: [https://github.com/Joevkadavan](https://github.com/Joevkadavan)
