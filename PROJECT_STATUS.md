# GOD’S EYE — Project Status

**Updated:** 2026-11-24 (Asia/Kolkata)  
**Workspace:** `/home/user/godseye`  
**State:** Existing FastAPI + Next.js application upgraded in place. The current registry contains two Chennai **image-refresh** embeds. This is a prototype, not an operational public-safety or emergency-response service.

## India camera upgrade — completed in this workspace

- [x] Preserved the existing app, UI style, FastAPI/SQLAlchemy backend, Next.js dashboard, YOLO video pipeline, event workflow, upload handling and settings.
- [x] Added camera fields for country/city, latitude/longitude, feed kind, source URL/attribution, refresh cadence, last health check, source image `Last-Modified`, and health message. Existing database tables receive additive columns at startup.
- [x] Added two Chennai camera records from OpenCCTV pages that explicitly provide official embed code. Coordinates were copied from each camera page’s location metadata. The UI links back to each source.
- [x] Added a separate asynchronous image-source health worker: it checks the direct JPEG endpoint (HTTP status, content type and JPEG signature), stores only health/timestamp metadata, marks the source unavailable on failure and retries automatically. It does **not** store, proxy, display, or run CV on the downloaded check bytes. The displayed imagery uses the provider’s official iframe embed.
- [x] Added city/feed filters, an India schematic map that plots only cameras with verified coordinates, source/status cards, refresh/update timestamps, provider attribution, and explicit `IMAGE REFRESH` labelling.
- [x] Still-image cameras are excluded from the video inference/tracking/events/metrics path. Person/vehicle detections and FPS show as unavailable (`—`) if there is no configured video source.
- [x] Removed the four bundled international demo-camera rows and their linked event/metric records during startup. Their media files remain solely as development/test assets; they are not seeded or presented as Indian/live feeds.
- [x] Added exact sidebar credit **MADE BY JOE V KADAVAN** (including a narrow-screen vertical treatment) and **Created by Joe V Kadavan** in the existing System Settings/About area. No new landing or login page was created.
- [x] Preserved title metadata `GOD'S EYE | Public Safety Intelligence`; updated the description to state the India-focused, verified-source and human-oversight scope.

## Source verification and limits

The health checks below were run on 2026-11-24 in the workspace. Each direct image endpoint returned HTTP 200, `image/jpeg`, and a JPEG signature. Both provider embed endpoints returned HTTP 200 HTML and permitted framing via `Content-Security-Policy: frame-ancestors *`. These are point-in-time endpoint checks, not a service-level guarantee.

| Camera | Location | Coordinates (WGS84) | Feed | Source / refresh |
|---|---|---:|---|---|
| Choolaimedu High Road | Chennai, Tamil Nadu | 13.06372, 80.23031 | Still image; roughly 10-minute provider refresh | [OpenCCTV page](https://opencctv.org/cameras/india/chennai-district/chennai/chennai-south-east-choolaimedu-high-road-302297) · official embed `/embed/302297` |
| Tiruvottiyur | Chennai, Tamil Nadu | 13.19230, 80.31570 | Still image; provider UI indicated about 150 seconds | [OpenCCTV page](https://opencctv.org/cameras/india/chennai-district/chennai/chennai-east-tiruvottiyur-313940) · official embed `/embed/313940` |

OpenCCTV identifies the cameras as third-party operated and disclaims affiliation/endorsement. Integration uses the embed code the directory provides and preserves its attribution; that is not proof of separate image-reuse or computer-vision rights from the camera operator. GOD’S EYE does not independently copy/store/process their image content. These are weather/public-view cameras, **not verified public-safety CCTV**. Endpoint availability does not mean continuous video, reliable uptime, or confirmed real-world scene conditions.

**No continuous Indian public CCTV stream has been verified or integrated.** A separately labelled Pexels prerecorded India traffic demo has since been added (its city is unverified; see Premium frontend status below). No other city is currently mapped. Still-image feeds cannot support temporal/motion claims, YOLO counts, or AI-generated event claims. An unavailable source is shown unavailable; no video is substituted. Broader integration should wait for source-owner authorization and a technically verified direct stream. Do not deploy persistent RTSP/CV workers to Vercel serverless functions.

## Architecture and behavior

- **Frontend:** Next.js 15 / React 19 / TypeScript / Recharts. Same-origin `/api/*` calls are rewritten by Next.js using `API_URL`.
- **Backend:** FastAPI, SQLAlchemy, SQLite locally / PostgreSQL option; long-running API process manages periodic health checks and authorized video workers.
- **Video AI:** Existing OpenCV + YOLOv8n ONNX CPU pipeline remains for separately configured, authorized video only. No facial recognition, biometrics, identity linkage, criminality prediction, or automatic external alerting.
- **Oversight:** Existing event cues require human verification. Image-refresh feeds produce no events, evidence images, inference metrics, or detections.
- **Deployment boundary:** Vercel can host the Next.js frontend, but the long-lived backend, database and any future RTSP/CV work need a persistent authorized backend. Configure `API_URL` to that backend; never point browser code at `localhost`. The Vercel connector returned no project matching “gods” in this session; **no Vercel deployment was made**.

## Tests and verification

- `cd backend && pytest -q`: **12 passed**, including new India registry/coordinates and JPEG health-check validation tests.
- `python3 -m py_compile backend/main.py backend/db.py`: passed.
- `cd frontend && npm run build`: passed after UI, map, and branding changes.
- Running FastAPI smoke test: `/api/health`, `/api/cameras`, `/api/india-feeds`, `/api/overview`, `/api/events`, `/api/analytics` returned HTTP 200; both India endpoints reported available after JPEG verification. Overview now separates video camera counts from image-source availability.
- Same-origin Next.js smoke: `/`, `/api/india-feeds` returned HTTP 200.
- Existing historical CV tests remain focused on bundled development video and synthetic temporal cases; these do not establish accuracy on Indian feeds or real incidents.

## Run / deployment instructions

### Local development

1. Start the persistent backend from `backend/` with the project environment and model installed: `uvicorn main:app --host 0.0.0.0 --port 8000`.
2. Start the dashboard from `frontend/`: `npm ci && npm run dev` (or `npm run start` after `npm run build`).
3. Keep the default local `API_URL` only for local development. Health-check workers run inside the backend and recover on subsequent checks.

### Docker Compose

Use the existing root `docker-compose.yml` and `.env.example`, set private local database credentials, then `docker compose up --build`. The backend container is the persistent worker; PostgreSQL is the database. Review the existing prototype security limits before any network exposure.

### Vercel frontend (not deployed here)

Deploy only `frontend/` as a Next.js project, set `API_URL` to the HTTPS origin of a separately hosted persistent backend, and verify the backend route/proxy and access policy. Do not run the periodic workers, RTSP ingest or CV inference as Vercel serverless functions. The present app has no authentication/RBAC and is not safe for unrestricted public exposure.

## Historical prototype performance (not India-feed measurements)

Before this upgrade, a 15-second run on the two bundled development clips measured 33.55 aggregate FPS mean, 90.2% mean system CPU and 220.5 MB max API RSS. Those results apply only to the old sample-video experiment; they do **not** describe the current still-image sources or establish deployment capacity. No accuracy metrics are claimed.

## Remaining work / limitations

1. Obtain and document direct camera-owner authorization before any image reuse, storage, or AI processing beyond the provider-supplied embed.
2. Find and verify authorized, technically accessible Indian continuous-video streams with exact coordinates and permitted purpose; add only after review.
3. Conduct a security review, add authentication/RBAC, access controls, TLS, rate limiting and deployment hardening before any public/network exposure.
4. Evaluate the existing video analytics on approved, labelled India-relevant data before making accuracy, incident, or operational claims.
5. Keep operator confirmation mandatory; event cues are not findings of danger or criminal intent.

## Fullscreen camera station upgrade (2026-11-24)

- [x] Added a responsive fullscreen monitoring view and entry points from feed cards and camera management. Existing routes and dashboard remain in place. The existing GOD’S EYE identity and **MADE BY JOE V KADAVAN** credit remain intact.
- [x] Added a no-cache synchronized video frame endpoint returning the same processed frame JPEG and the exact timestamp, bboxes/classes/confidence/temporary track IDs and metrics produced from it. The browser displays that exact frame; the standard overlay is rendered server-side on the image itself to avoid scaling/letterbox misalignment. Raw-frame view is also available.
- [x] Frame-driven people/vehicle/class/confidence/tracking summaries, activity, and rolling FPS/object/latency charts. A missing/failed frame clears current data rather than presenting stale detections as current. Screenshots carry camera, location, timestamp, source state, model and observed count metadata.
- [x] Added camera switching, keyboard shortcuts, responsive intelligence sidebar, source attribution and explicit error/connecting/offline states. Chennai sources remain provider-served `IMAGE REFRESH` with no video or AI inference. Local files are `DEMO`; a continuous configured video source is called `LIVE` only while current frames arrive. No unsupported browser playback, mute, or quality controls were added.
- [x] Corrected telemetry to report GPU utilization as `null` when unavailable instead of reusing CPU utilization; actual CPU, memory, model version, runtime provider and ONNX metadata stay separately identified.
- [x] Added a detector-backed synchronized-frame integration test to backend suite.

### Fullscreen verification

- `cd backend && pytest -q`: **9 passed**, including the new frame/JPEG/detection synchronization integration test using the real YOLOv8n ONNX model and bundled test clip.
- `python3 -m py_compile backend/main.py backend/db.py`: passed.
- `cd frontend && npm run build`: passed (Next.js optimized build and TypeScript validity).
- End-to-end live API exercise added an authorized local prerecorded test clip, received HTTP 200 from the synchronized endpoint, decoded a **768×432** JPEG, and verified it had the identical timestamp and a real YOLO person detection/temporary track ID with in-bounds bbox; the temporary camera was removed. This is correctly a **DEMO**, not public LIVE CCTV.
- Dashboard `/` plus backend `/api/health`, `/api/cameras`, and `/api/overview` smoke requests returned HTTP 200. Health reported YOLOv8n ONNX 8.3.78, 416 input, `CPUExecutionProvider`, and null GPU utilization.
- Fullscreen CSS passed brace/class sanity checks. No Chromium/Firefox or Playwright/Puppeteer browser automation was installed, so responsive layout and interactive keyboard flows were build-checked but not visually automated in-browser.
- No continuous public Chennai feed has been verified: the two integrated sources continue to be provider iframe image-refresh embeds only. Public-video operation and public-feed rights are not claimed.

## Premium frontend + licensed Indian prerecorded demo (2026-11-24)

- [x] Kept the existing Next.js dashboard/routes/components, React/Recharts charts, backend APIs, feeds, YOLO overlays, and the creator credit **MADE BY JOE V KADAVAN**. No new animation library was installed: the project had none, so the redesign uses lightweight CSS keyframes/transitions and a small `requestAnimationFrame` numeric counter, with reduced-motion support and no 3D/particle dependency.
- [x] Added a one-time, skippable cinematic GOD'S EYE intro; restrained grid/ambient scan backgrounds; staged page/card and camera-hover transitions; number easing; live/status indicator motion; and subtle viewer scanning. Motion is primarily opacity/transform and is disabled/respects `prefers-reduced-motion`.
- [x] Removed the redundant fullscreen icons from camera cards and management rows. The plain-text **OPEN STATION** button still opens the existing fullscreen viewer; only one exit-fullscreen control remains in that viewer. No empty icon buttons remain.
- [x] Downloaded and packaged an Indian urban traffic clip: Pexels video 5009674 by Meenakshi Vinay Rai, 1920×1080, 25 fps, 21 s. Pexels' source page identifies daytime India traffic with cars, bikes and pedestrians; its License page permits free use under listed terms. The city is **not verified**: the seeded camera has country India only, no Chennai claim or map pin. Media/license details are recorded in `data/media/INDIAN_DEMO_ATTRIBUTION.md` and `data/media/ATTRIBUTION.md`.
- [x] The API seeds **GOD'S EYE – Indian Urban Traffic Demo** as an enabled, explicitly prerecorded `DEMO` file and opens it through the same continuous OpenCV + YOLO worker as authorized video sources. The viewer presents the worker's synchronized frame/JPEG and actual detections; video transport remains sampled processed frames (not a separate browser video that could drift from inference). Added backend pause, resume and replay controls; pause holds a fixed processed frame/telemetry, and replay seeks the decoder to zero and resets camera-local track state. The progress bar/timecode use actual decoder position/duration. Full-screen browser controls remain available.
- [x] Demo status is never `LIVE`; it is `DEMO` / `PRERECORDED YOLO DEMO`. The viewer credits the Pexels creator and links the license. Current accuracy is not implied by the sample: detections are ordinary COCO YOLO model outputs, not labelled ground truth.

### Demo and redesign verification

- Pexels page `/video/vehicles-on-the-road-in-india-5009674/` was fetched; direct MP4 URL returned **HTTP 200 video/mp4**, 14,323,936 bytes. The local 21-second video was decoded successfully by OpenCV at 1920×1080, 25 fps.
- Real ONNX YOLOv8n inference on the first demo frame detected **person** and multiple **cars** (plus a truck); all returned boxes stayed within original-frame dimensions. The demo viewer/backend returns that source image and metadata from the same processed frame.
- Running API integration verified the demo camera is seeded as `DEMO`, current processed frame returned HTTP 200 at 1920×1080 with person/car/truck detections, model FPS/latency and frame timestamp. Pause was verified to hold the same timestamp after worker quiescence; resume advanced timestamps; replay invalidates stale cached frames and returned to decoder position near zero. With CPU frame dropping enabled, decoder time advanced about 1.16 seconds during a 1.2-second wall-clock sample on this workspace.
- Backend tests: `cd backend && pytest -q` → **12 passed**, including real YOLO inference on the licensed Indian clip and playback action validation. Frontend: `cd frontend && npm run build` passed after final responsive styles, demo controls, copy and metadata. Same-origin dashboard/API HTTP smoke requests also passed. No Chromium/Firefox/Playwright runtime was available for visual desktop/mobile or browser-console automation; responsive CSS and keyboard behavior are build/sanity-checked, not claimed as visually browser-tested.
- The source is a short stock traffic scene, not a live feed. It is **India-origin per its Pexels description**, but there is no verified Chennai location. Do not claim Chennai-specific activity, location-specific incidents, or measured detection accuracy.

## Interactive map and situational-awareness audit upgrade (2026-11-24)

- [x] Completed and saved the expanded frontend audit at `docs/frontend_audit_2026-11-24.md`; prioritized feed-denominator ambiguity, alert lifecycle noise, false event ordinal “frequency,” uncontrolled verification filter, schematic map limits, camera card overlays, over-fast polling, and missing-metric zero substitution.
- [x] Replaced the schematic India SVG with a MapLibre interactive map, source-coordinate-only markers, available/unavailable filtering, keyboard-accessible source picker, boundary toggle, reset/zoom and optional pitch/building extrusion. The subsequent map implementation pass moved the state/UT reference overlay from generalized Natural Earth to simplified geoBoundaries gbOpen ADM1 GeoJSON; provenance and non-legal-boundary caveat are in `docs/geospatial-map.md`. No city/place gazetteer locations are converted into monitored-camera pins.
- [x] Improved camera card hierarchy, source-status labels, source embed reload control, source freshness notes, demo disclosure, responsive map controls, icon micro-motion/reduced motion and unavailable/loading states. Dedicated OPEN STATION/fullscreen flow remains.
- [x] Made the incident verification state filter functional and hardened action error reporting. Removed demo startup lifecycle events from alert generation; informational lifecycle history is excluded from actionable pending alert counts but retained historically. The original `/api/analytics.event_frequency` event rows are preserved; a new additive `event_frequency_buckets` field groups actual stored events into populated UTC hour buckets. The 1/6/24-hour UI filters cover real persisted samples only.
- [x] Separated India registered source denominator from demo feed counts; display `—` instead of fabricated missing metrics; made the dashboard poll data every 10 seconds while maintaining the clock separately.
- [x] Updated Next.js to 15.5.29 and MapLibre GL JS to security-patched 6.4.1, PostCSS to 8.5.33 via override. `npm audit` now reports 0 vulnerabilities. Existing backend routes, response envelopes, database architecture, YOLO processing and media data remain in place.
- [x] Added asset generator, audit/provenance/implementation docs, backend event-history tests and geospatial asset validation.

Verification for this pass: `frontend/npm run build` passed with Next.js 15.5.29, TypeScript and MapLibre GL JS 6.4.1; `frontend/npm audit` found zero vulnerabilities; `backend/python3 -m pytest -q backend/tests` passed **16/16**. Runtime smoke checks of API health, overview, analytics, same-origin API proxy, dashboard page and public GeoJSON all returned HTTP 200. Overview reported zero actionable pending alerts while historical informational DEMO rows remain in the ledger. Automated browser visual/runtime checks remain unavailable because the workspace has no supported browser automation binary; external map tiles need a network-capable browser.

## Brand mark, responsive navigation, immersive still-image station viewer (2026-11-24)

- [x] Added the creator credit to the top-left product lockup and mobile header.
- [x] Replaced the plain brand eye with a CSS/SVG dimensional metallic-cyan mark, subtle iris drift, non-flashing irregular blink timer, hover parallax and active glow. No 3D graphics package added; reduced-motion preferences disable animation.
- [x] Added tablet slide-in navigation and mobile bottom navigation; stacked camera cards, two-column KPI layout, safe-area padding, mobile map touch controls, responsive viewer panel, and landscape-specific rules.
- [x] Made camera images open the fullscreen camera station with selected-source name/location, availability, exact registry coordinates, OpenCCTV source/embed, classification, periodic refresh metadata, last check and last image timestamp. Added hide/show-information desktop side panel/mobile sheet. Still-image warning is explicit; iframe/source links remain provider-controlled. Escape, close, outside-layout click and scroll restoration are implemented.
- [x] Verified live API metadata: Choolaimedu High Road 13.06372, 80.23031, 600 sec; Tiruvottiyur 13.19230, 80.31570, 150 sec. No camera API/data changes made.
- [x] Final `frontend/npm run build` passed; `npm audit` found 0 vulnerabilities; backend tests remain **17 passed**. Dashboard, overview/analytics, map asset and health smoke calls returned HTTP 200.
- [ ] Manual visual browser checks at 360/390/430/tablet widths, landscape, both modal selections, and browser-console errors remain outstanding because no Chromium/Chrome/Firefox/Playwright executable is available. See `docs/branding-mobile-viewer-2026-11-24.md` for the transparent test limits.

## Cinematic landing hero for the Indian traffic demo (2026-11-24)

- [x] Promoted the existing bundled Pexels Indian Urban Traffic MP4 to the main Overview hero immediately beneath the website header. Kept the original station/viewer workflows; this adds seekable browser video for the homepage rather than replacing the YOLO station's processed-frame viewer.
- [x] Added restricted demo-only MP4 delivery, byte-range seeking through the Next.js same-origin API proxy, a lightweight actual-inference telemetry endpoint and client alignment between browser playback position and backend processed-frame position. Bounding boxes are rendered only when position is within sync tolerance; otherwise the UI reports syncing rather than implying a current overlay.
- [x] Added muted autoplay, loop, mobile inline playback, play/pause, replay, volume, fullscreen, buffering/error treatment, source/status branding, people/vehicle/inference FPS stats, YOLO status, Pexels attribution and explicit “prerecorded / not live CCTV / city not verified” language.
- [x] Ordered the Overview content under the hero as KPIs → Verified India Camera Views → Interactive 3D India Map → Alerts Requiring Review → Activity Snapshot → Recent Events; responsive hero and touch-friendly control styles include reduced-motion handling.
- [x] Final-state frontend production build passed. Backend tests: **18 passed**. Runtime homepage returned HTTP 200. Live telemetry returned actual worker detections and metrics. A 1,024-byte `Range` GET through Next.js returned HTTP **206 Partial Content**, `video/mp4`, inline disposition and `Accept-Ranges: bytes`.
- [ ] Desktop/mobile visual viewport inspection and measured horizontal overflow checks remain outstanding: this workspace has no Chromium/Firefox binary and no Playwright/Puppeteer installation. The live dashboard preview is running for final visual QA. Implementation/test detail: `docs/prerecorded-demo-hero-2026-11-24.md`.

## Free 3D MapLibre/OpenStreetMap India map upgrade (2026-11-24)

- [x] Retained MapLibre GL JS + OpenFreeMap/OpenMapTiles vector tiles and switched to a dark intelligence style by default; added Liberty, Positron, Bright style selection. Pan/zoom, drag rotation/tilt, fullscreen and reset-to-India controls are provided.
- [x] Added optional map-city navigation (cities are fly-to destinations only, never camera pins), interactive GeoJSON camera layers, restrained illuminated status halos, source availability and stored last successful image-refresh timestamp, and an Open Camera action that invokes the existing station viewer.
- [x] Added a 3D extrusion layer for mapped OpenMapTiles/OSM buildings at high city zooms; buildings display only where footprints/heights exist in the current tiles. Uses GeoJSON admin-1 lines for states/UTs. No default satellite imagery; a style option only appears with `NEXT_PUBLIC_SATELLITE_STYLE_URL` configured.
- [x] Swapped the earlier Natural Earth generalized overlay for a locally bundled, simplified 36-feature geoBoundaries gbOpen India ADM1 GeoJSON (CC BY 4.0 attribution), generated by `scripts/build_india_admin1.py`. The overlay is explicitly reference-only and not a legal boundary authority.
- [x] Lazy-loads MapLibre near viewport, avoids map recreation on data updates, handles style reloads and tile/boundary errors, retains provider attribution, and documents OpenFreeMap free public instance terms (no map-view/request quota as published, no SLA/uptime promise; offline downloads capped at 3,000 tiles / 50 MB / four concurrent requests).
- [x] Verified `npm run build` passes and `python3 -m pytest -q backend/tests` gives **18 passed**. Local runtime: homepage, same-origin API, and GeoJSON return HTTP 200; GeoJSON has 36 features and 1.29 MB; verified Chennai registry coordinates and `last_image_at` are passed through.
- [ ] Vercel production test is blocked: connected Vercel account has no GOD'S EYE project; its only project, `bealwaysjoe`, serves an unrelated creator-services website. I did not deploy to or alter that production project. GOD'S EYE also requires `API_URL` to point to a reachable deployed FastAPI backend; the local 127.0.0.1 default will not work on Vercel. Need the correct Vercel project/repository and API URL before production test.

## Final branding and source-publication preparation (2026-11-24)

- [x] Kept the animated SVG/CSS eye intact. Promoted the exact **MADE BY JOE V KADAVAN** credit alongside the top-left brand on desktop, tablet/mobile, and the brief first-load intro; kept **PUBLIC SAFETY INTELLIGENCE** visible on all lockups. Removed the lower About-panel duplicate and obsolete footer/intro credit styling.
- [x] Added the requested independent root documents `PROJECT_OVERVIEW.md` and `HOW_I_BUILT_GODS_EYE.md`, plus `frontend/vercel.json`. Updated README map/video/deployment sections, `.gitignore` and `.env.example` handling. Environment files other than safe examples, build outputs, local DB, evidence, uploads and Vercel credentials are excluded.
- [x] Current verification: final frontend `npm run build` passed; backend tests **18 passed**; local dashboard, `/api/overview` and GeoJSON returned HTTP 200; verified the two Chennai registry coordinates and recorded image timestamps; staged-file secret-pattern scan found no credential tokens.
- [x] Workspace had no Git repository or commits; initialized a truthful local `main` branch and recorded one actual source snapshot commit: `eb898d9` (`Prepare GOD'S EYE dashboard source and launch documentation`). 64 project files, including source, tests, maps, ONNX models and attributed media, are committed locally. No prior history was rewritten.
- [ ] GitHub publication is blocked by authentication: public API lookup for the requested repository returned 404 (could be absent or private); no GitHub CLI, authenticated git remote or token is available, and Arena's GitHub connector is unsupported. No remote repo was created or overwritten and nothing was pushed. Need an approved authenticated GitHub publishing path.
- [ ] Vercel production deployment remains pending. The connected account lists no `gods-eye-dashboard` project; its only project is `bealwaysjoe`, a separate site. The preferred `gods-eye-dashboard.vercel.app` currently serves an unrelated Cyber Chief site. `godseye-dashboard-joevkadavan.vercel.app` returned Vercel `DEPLOYMENT_NOT_FOUND` at check time and is a candidate only, not reserved.
- [ ] Production also requires a persistent FastAPI host and `API_URL`; Vercel cannot run the app's long-lived OpenCV/ONNX camera workers in the Next.js deployment. API mutation routes currently have no authentication, so before publishing the connected API publicly we need either operator authentication or a read-only public API policy. No external paid hosting or paid map source was chosen.
- [ ] No graphical browser runtime was available for final desktop/mobile viewport testing. See `HOW_I_BUILT_GODS_EYE.md`, Step 11, for test scope and limitations.

## FastAPI connectivity and real demo analytics validation (2026-11-24)

- [x] Inspected the existing API lifespan and worker pipeline before changing code. Confirmed ONNX model, bundled MP4 and enabled demo registry entry exist. Initial runtime inspection found the frontend on port 3000 but no GOD’S EYE listener on port 8000; there was no model/import/startup fault. Started the existing `main:app` FastAPI service successfully; its lifespan loaded the existing ONNX YOLO model and relaunched the prerecorded demo camera worker.
- [x] Made `/api/health` distinguish API health/model readiness from actual inference freshness: adds `inference_status` (`PROCESSING`/`WAITING`), `processing_cameras`, and `active_video_workers`. Processing status is based on actual latest worker samples no older than 30 seconds, with a 60-second future-timestamp tolerance.
- [x] Tightened Overview person/vehicle/FPS presentation to require a fresh inference sample rather than equating an online source with active analytics; absent/stale metrics show an em dash. On API failure, stale dashboard data is cleared, actual HTTP status is shown when available, and the existing 10-second polling reconnect remains. The error guidance now covers either local FastAPI or deployed `API_URL` configuration.
- [x] After stopping and restarting the API, confirmed successful model load, demo-camera recovery to `online`, `/api/health` `PROCESSING`, `active_video_workers: 1`, actual telemetry and 1920×1080 synchronized frame responses. `/api/health`, `/api/overview`, `/api/cameras`, `/api/analytics`, telemetry, frame, MP4 and same-origin Next.js proxy returned HTTP 200. The MP4 accepted a real byte-range request (206; 1,024 bytes). Playback pause/play/replay each returned 200.
- [x] Latest verification: `backend/pytest -q` **22 passed**; `frontend/npm run build` passed.
- [ ] No connected GOD’S EYE Vercel project or deployed persistent API origin was available. The connected Vercel project `bealwaysjoe` is unrelated and was not changed. Production API connectivity remains untested; configure Vercel `API_URL` only after a persistent, publicly reachable, secured FastAPI deployment exists. The prototype still has no API authentication/RBAC.
- [ ] Interactive browser visual testing and API-disconnect UX testing were not performed; local API restart recovery was verified directly at the service level.

## Hydration stability and map context (2026-11-24)

- [x] Fixed SSR/client clock mismatch by rendering a stable clock/date placeholder, setting the clock only after mount, and formatting it in `Asia/Kolkata`. Added root-level hydration-warning suppression for browser extensions that inject attributes into `<html>` before React hydrates.
- [x] Added a compact India map scope note: only registry-verified coordinates are plotted; Chennai pins are periodic still-image sources, not continuous CCTV/AI feeds; the demo video has no verified city and is not represented as a camera pin.
- [x] Added dynamic map summary cards for plotted coordinate count, available/unavailable source counts, verified place names and image-refresh/video source mix. Values derive from the verified camera registry.
- [x] Added a geographic-coverage insight that summarizes the currently mapped places and clearly distinguishes source checks from continuous video/AI processing; copy updates from live registry data.
- [x] Verified the production build and generated HTML contains the map context, summary labels and matching pre-hydration date placeholder.
- [x] Replaced source-startup rows in the visible incident register with timestamped traffic observations sourced from actual persisted YOLO samples (vehicle/person-class counts, measured FPS and estimated vehicles/minute); removed source lifecycle rows from the visible event state and analytics distribution. Renamed the camera display label to `GOD'S EYE – Indian Urban Traffic` and removed the visible demo branding.
- [x] Kept source provenance explicit: the UI states that the video is not a live CCTV stream; no live-feed claim is made. Revalidated with 22 backend tests, frontend production build, live API health/inference status, renamed registry camera, actual metric samples, and HTTP 200 dashboard/API routes.

## Public-launch follow-up (2026-11-24)

- [x] Restored the video-first dashboard as the `/` landing route (redirecting to `/operations`); the Chennai source-availability page remains at `/chennai`. Preserved the eye animation and added the exact developer credit to the dashboard's top-left desktop/mobile brand and first-load lockup; removed no working dashboard panels.
- [x] Hardened the root document hydration handling and made the landing route a server redirect. A production-build Chromium smoke test visited `/`, `/operations`, and `/chennai` with no browser page errors or hydration console errors. At 390 px width, `/` and `/chennai` had no horizontal overflow. The dashboard video element rendered and the Chennai page rendered two source cards.
- [x] `cd frontend && npm run build` passed; `cd backend && pytest -q` passed **22 tests**. Same-origin `/api/india-feeds` returned HTTP 200. The source list, actual demo-video telemetry, dashboard navigation, and mobile brand credit were exercised in the browser.
- [x] Preserved the original local Git history and committed the final source update to `main` as `038dd84` (`Finalize video-first landing page and launch documentation`). Subsequent QA and Render/Supabase deployment preparation have also been committed; after this status update, the local `main` branch will have six truthful commits and a clean working tree, with no Git remote configured.
- [x] Created a new Vercel project named `gods-eye-dashboard` with framework `nextjs`, root directory `frontend`, install command `npm ci`, and build command `npm run build`. The unrelated `bealwaysjoe` project was not touched.
- [ ] GitHub publication is still blocked: the requested repository URL returned HTTP 404 to an unauthenticated API lookup (private existence cannot be ruled out); no GitHub connector or CLI/authenticated remote is available. No remote repository was created and no push has happened. The two requested Markdown files are present in the local project root.
- [ ] Vercel has no source connection or deployment for the new project yet. `https://gods-eye-dashboard.vercel.app` returns the unrelated “God's Eye | Cyber Chief” site, so it must not be used or overwritten. The new Vercel project currently inherits SSO protection for all non-custom-domain deployments; public access needs a domain/protection change and verification. No public production URL is claimed.
- [ ] Production API data requires a persistent, secured FastAPI backend and its public origin configured as Vercel `API_URL`; no such URL was supplied. No credentials were exposed. The GitHub connection, backend host, and public-domain/protection setup remain approval/configuration prerequisites.

## Free Render + Supabase backend preparation (2026-11-24)

- [x] Added root `render.yaml`: Python web service on Render `free`, `rootDir: backend`, `pip install -r requirements.txt`, `uvicorn main:app --host 0.0.0.0 --port $PORT`, `/health`, automatic commit deploys, and secret prompts for `DATABASE_URL` / `FRONTEND_ORIGINS`.
- [x] Added `/health` with a database connectivity check; retained `/api/health`, `/api/overview`, and `/api/india-feeds`. Local smoke checks returned HTTP 200 for all four routes.
- [x] Production database setup now normalizes Supabase PostgreSQL URLs to psycopg v3, requires TLS in production, limits pool size, and rejects SQLite on Render/production. The Render blueprint leaves DB credentials as an unset secret; no password or URL with credentials is committed.
- [x] CORS now uses exact comma-separated `FRONTEND_ORIGINS`; production rejects wildcard/local-only origins and requires the actual HTTPS Vercel origin to be set when creating the Render service.
- [x] Free Render defaults turn off video inference, local uploads, and local evidence files; the full OpenCV/ONNX implementation remains available for local or higher-capacity deployments. The Overview API returns null counts/FPS when there is no actual current inference, never synthetic zero metrics. Free-tier retention is set to 30 days for database rows.
- [x] `cd backend && pytest -q`: **30 passed** (including URL normalization, SQLite prohibition, CORS parsing, no-inference count, evidence-storage, and health behavior). Production frontend build remains successful.
- [ ] No Render account connector is available in this session, and Supabase is not connected. No Render service or Supabase project/database was provisioned; the HTTPS service URL and Vercel `API_URL` therefore remain unknown. The supplied repo cannot yet be authenticated/connected to Render because GitHub access is also pending.
- [ ] Free-tier limitations are material: Render Free is a single 0.1 CPU / 512 MB instance, has ephemeral local disk, and spins down after inactivity; Supabase Free may pause after low database activity. The deployment therefore serves the API and durable Postgres records, but does not promise continuous inference. Current UI/API must leave inference figures unavailable unless fresh samples are really returned.
