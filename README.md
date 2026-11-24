# GOD'S EYE

**A privacy-conscious, human-verified video analytics capstone prototype.** This repository builds a working local command-centre dashboard and CPU inference service. It does not identify people, infer criminal intent, decide that a person is dangerous, or contact emergency services.

## Current implementation

- Dynamic-shape YOLOv8n COCO detector on ONNX Runtime CPU; class-aware NMS and bounding boxes.
- Camera-local temporary IoU track IDs; people/vehicle counts, crowd thresholds, FPS/latency and simple traffic flow proxy.
- Temporal motion/posture cue for possible falls (rapid downward displacement followed by a sustained horizontal box); stationary-object duration and image-plane unusual-motion cues. These are **unvalidated heuristics** and must be treated as suggestions for operator review, not robust incident classifiers.
- Independent async workers for local files, webcam, authorised RTSP sources; shared serialized model session and bounded default camera startup.
- Alert persistence with event UUID, camera, category, timestamp, confidence, description, severity, verification status and short-lived JPEG evidence; acknowledge/verify/dismiss controls.
- 10-second metric history with retention cleanup; upload and evidence expiration.
- Next.js/React/TypeScript dashboard with Overview, Live Monitoring, Incidents, Analytics, Cameras and Settings; Recharts visualisations, camera CRUD, validated settings, reusable restrained icon motion, and responsive source/status cards.
- Lazy-loaded MapLibre India map with a selectable OpenFreeMap/OpenStreetMap vector style, locally bundled geoBoundaries state/UT GeoJSON, OSM-derived building extrusions, city navigation, fullscreen/tilt/rotation, and selectable registered camera markers that open the existing station viewer. Only registry camera coordinates are plotted; source, licensing, usage-limit and boundary caveats are documented in `docs/geospatial-map.md`.
- FastAPI REST/OpenAPI plus WebSocket updates. Dashboard polls same-origin REST endpoints every 10 seconds (plus a local 1-second clock); WebSocket remains available to API clients.
- SQLite by default, PostgreSQL through `DATABASE_URL`.

**Not yet implemented/validated:** pose-based fall classification (a dynamic pose model is supplied but not run in default CPU pipeline), vehicle line-crossing calibration, robust density estimation for severe occlusion, adaptive inference cadence, dataset fine-tuning, labelled accuracy metrics, authenticated multi-user access, TLS, and edge-hardware testing. See `PROJECT_STATUS.md` and `docs/evaluation.md` before presenting capabilities.

## Requirements / tested target

- Python 3.13 and Node.js 20+
- About 2 GB RAM is enough for the local prototype, but inference is CPU-bound. A GPU is not required.
- Tested in this workspace on 2 CPU cores / no GPU. A 320 or 416 px model input is recommended for CPU.

## Quick start (local development)

```bash
cd godseye
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env

# Terminal 1: API and documented OpenAPI UI
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2
cd frontend
npm ci
npm run dev
```

Open `http://localhost:3000` (dashboard) and `http://localhost:8000/docs` (interactive API). The dashboard proxies `/api/*` requests through Next.js, so browser code uses relative URLs. Do not add unauthorised CCTV feeds. The India registry currently contains two Chennai still-image views embedded from OpenCCTV (with source credit and verified coordinates). They are labelled `IMAGE REFRESH`, health-checked periodically, and are not continuous video or processed by the YOLO pipeline. No verified continuous Indian public video stream is currently configured. The old bundled international sample cameras are removed from the camera registry at startup; they are never relabelled as Indian/live.

### Settings and persistence

`backend/.env.example` lists the runtime environment variables. Camera/alert settings can also be edited in System Settings; validated values are persisted to `data/settings.json` and applied at runtime. The default local DB is `data/godseye.db`. For PostgreSQL, set `DATABASE_URL=postgresql+psycopg://...` in `backend/.env`.

`RETENTION_HOURS` (default 24) expires event records, JPEG evidence and uploaded videos. The legacy Intel clips in `data/media/` remain test assets and are not automatically added. The separately licensed Pexels Indian-traffic clip is the exception: the API seeds it as an enabled, prerecorded `DEMO` camera and runs it through the real YOLO pipeline. See `data/media/INDIAN_DEMO_ATTRIBUTION.md`. Generated evidence/settings/database/uploads are local runtime data and should not be committed.

### Add sources

- **Local sample/uploaded video:** Camera Management page or `POST /api/cameras/upload`. Direct file paths are restricted to `data/media/` and `data/uploads/`.
- **Webcam:** `POST /api/cameras` with `{"name":"Local webcam","source":"0","source_type":"webcam"}`.
- **RTSP:** `POST /api/cameras` with an authorised `rtsp://...` URL and `source_type:"rtsp"`. Do not store credentials in source control; use an authorised, secured network and avoid exposing RTSP publicly.

## Vercel frontend (deployment pending)

The Next.js frontend is configured for Vercel in `frontend/vercel.json`, but no GOD'S EYE production deployment has been completed. The FastAPI process and periodic health-check workers must run on a persistent backend. Set the production `API_URL` to that reachable backend origin so Next.js rewrites `/api/*` server-side; the local fallback `127.0.0.1:8000` will not work on Vercel. Do not put persistent RTSP/CV workers in serverless functions. This prototype has no authentication/RBAC and must not be exposed as an unrestricted operational public-safety service. The requested `gods-eye-dashboard.vercel.app` host currently serves an unrelated Cyber Chief site; do not overwrite it.

## Docker (optional)

Docker Compose starts PostgreSQL, FastAPI and the dashboard. Set private local credentials in an untracked `.env` copied from `.env.example`:

```bash
cp .env.example .env
# Replace the example password locally
# then:
docker compose up --build
```

The backend image includes the ONNX runtime model and legacy test clips; only the verified India image-refresh registry is initialized automatically. GPU acceleration is not configured because the verified prototype target is CPU-only.

## Model files and reproducibility

Included model files:

- `backend/models/yolov8n.onnx` — dynamic H/W FP32 detector (12.7 MB)
- `backend/models/yolov8n.int8.onnx` — dynamic weight-only INT8 alternative (3.2 MB, **slower on tested CPU**)
- `backend/models/yolov8n-pose.onnx` — dynamic pose export (optional; not used by default pipeline)

The dynamic detector was compared with a static 640 export of the same checkpoint: max/mean absolute difference were exactly 0 on a seeded 640×640 input. Detection and pose ONNX shapes were smoke-tested at 320, 416 and 640.

Build-time export requires PyTorch and Ultralytics; they are intentionally not in runtime `requirements.txt`:

```bash
pip install 'torch==2.9.1+cpu' 'ultralytics==8.3.78' onnxscript onnx onnxruntime
cd backend
python tools/export_models.py
```

The script exports dynamic detector and pose models and quantizes YOLOv8n weights. Model licensing (including Ultralytics AGPL/commercial terms) must be reviewed before redistribution or commercial deployment.

## Tests and measured results

```bash
cd backend
pytest -q
python tools/benchmark.py --frames-per-clip 20
```

The test suite exercises IoU, temporary tracking IDs and ONNX inference. Latest test results and API smoke checks are recorded in `PROJECT_STATUS.md`. Benchmark CSV/JSON are under `data/evaluation/`. The four demo videos have no ground-truth labels here; precision, recall, F1, mAP, false alarm and miss rates are **not claimed**. All actual timing numbers and their limitations are in `docs/evaluation.md`.

## Research and responsible use

- Architecture: `docs/architecture.md`
- Literature, research gaps, proposed contribution, dataset terms: `docs/research_review.md`
- Project proposal and provisional academic manuscript: `docs/project_proposal.md`, `docs/research_paper_draft.md`
- Real measurements and pending evaluation protocol: `docs/evaluation.md`
- Project progress and known limitations: `PROJECT_STATUS.md`
- Faculty demo outline: `docs/demo_script.md`
- Provisional PowerPoint briefing: `docs/faculty_briefing.pptx` (source generator `docs/build_briefing.py`)

The supplied Intel IoT sample clips repository labels the videos CC BY 4.0; attribution is in `data/media/ATTRIBUTION.md`. Other public datasets are not included and should only be obtained after checking current primary-source terms. Human verification is mandatory, raw video is not retained by default, and there is no automated external alerting.

## Indian urban traffic demo

The Overview hero plays the bundled licensed Pexels clip `data/media/indian-urban-traffic-pexels-5009674.mp4` through a seekable same-origin MP4 route. It is visibly labelled prerecorded `DEMO`, never live CCTV; the Pexels page identifies India traffic but does not verify a city, so it has no camera/map coordinates. Muted autoplay, looping, play/pause, restart, volume and fullscreen control the browser video. Separately, the backend's OpenCV worker runs YOLOv8n ONNX on the same source; the hero polls actual telemetry and draws boxes only when browser and worker media positions align (otherwise it hides boxes and reports syncing). The existing fullscreen station still displays backend-processed frames and their matching detections. Source URL, creator and license are in `data/media/INDIAN_DEMO_ATTRIBUTION.md`.

## Fullscreen monitoring station

The Live Monitoring dashboard and Camera Management page provide a fullscreen viewer for configured feeds. For authorized video/webcam/RTSP sources, the viewer polls `GET /api/cameras/{camera_id}/frame?overlay=true|false`, an uncached API response containing the JPEG plus the exact timestamp, inference detections (class, confidence, bbox, ephemeral camera-local track ID), and metrics generated from that same frame. The default display uses the backend-rendered overlay, avoiding independent browser box scaling/letterboxing drift; toggle overlays to inspect the raw frame. Frame-derived counts, activity, and rolling performance charts clear on disconnect and are never populated with sample/fabricated values. Screenshots include the source state, model, frame time, camera/location, and observed counts.

Fullscreen is a responsive station with camera switching, source state, model/runtime metadata, confidence and class summaries, and keyboard shortcuts (`F`, `D`, `I`, arrow keys, `Esc`). The station viewer itself remains a synchronized processed-frame viewer and therefore has no audio/quality controls; the separate Overview landing hero provides native browser-video playback, audio, replay and fullscreen controls for the prerecorded demo. `DEMO` denotes operator-configured prerecorded files; a continuous video source is `LIVE` only while the processed-frame endpoint is returning current frames. The Chennai provider embeds remain `IMAGE REFRESH`, with no YOLO/tracking/performance claims. GPU utilization is reported as `null` unless a real supported measurement is available; CPU usage is separately labelled.

Verification in this workspace: `cd backend && pytest -q` (9 passed), backend syntax checks, and `cd frontend && npm run build`. A real authorized local demo clip was added temporarily and exercised end-to-end: the API returned a 768×432 JPEG and its matching current YOLO person detection/track ID; returned boxes fell within frame dimensions; the temporary camera was deleted afterward. No continuous public Chennai video feed is verified, and no graphical browser automation was available. The live preview can be tested manually with an authorized local video source; image-refresh embeds intentionally remain provider-served.
