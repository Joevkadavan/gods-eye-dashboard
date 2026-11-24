# GOD'S EYE — Capstone Proposal (Working Draft)

## Abstract
GOD'S EYE is a local-first video analytics prototype that processes authorized camera feeds, detects common objects, maintains short-lived camera-local tracks, reports crowd/traffic statistics, and surfaces temporally qualified observable cues for human review. Its first deployment target is a conventional CPU-only development computer, not a cloud GPU or purchased edge device. The engineering contribution is an auditable camera-to-alert pipeline with configurable compute/retention controls; the research hypothesis is that a resource-budgeted camera-local temporal evidence policy can reduce unnecessary inference while keeping event delay and review quality measurable. This proposal does not claim that the present prototype is accurate enough for operational emergency response. Dataset access and human review are required before any performance or novelty claim.

## Problem statement
Manual CCTV review does not scale well across multiple feeds, while single-frame object classification cannot establish an event such as a fall, collision, unattended object or sudden crowd movement. Video analytics also introduce privacy, false-alarm, and compute constraints. The prototype should convert video into limited observable events and statistics while preserving human authority and avoiding identity or intent inference.

## Objectives
1. Build a working multi-source video pipeline with YOLO object detection, temporary object tracking and per-camera throughput monitoring.
2. Produce crowd and traffic measurements and implement configurable thresholds.
3. Implement at least one temporal event cue and distinguish it from single-frame classification.
4. Create persistent alerts with evidence and explicit human acknowledgement/verification/dismissal.
5. Build Overview, Live Monitoring, Incidents, Analytics, Cameras and Settings pages backed by real REST APIs.
6. Measure actual CPU inference and memory trade-offs across input size and quantization.
7. Establish a permission-aware dataset and event-level evaluation plan before accuracy claims.

## Scope and exclusions
Included: authorized webcam, uploaded/local files, authorized RTSP; COCO detector classes; temporary camera-local IDs; configurable count thresholds; weak temporal cues; short-lived evidence; human decision states; SQLite/PostgreSQL storage; responsive web UI.

Excluded: face recognition, re-identification, person identity or demographic inference, criminality/dangerousness prediction, automatic external alerting, unlimited video archive, unauthorised feed discovery, medical fall diagnosis, unreviewed police/emergency integration.

## System architecture and methods
See `architecture.md`. The current detector is YOLOv8n exported dynamically to ONNX and executed through CPU ONNX Runtime. Preprocessing letterboxes to operator-selected size; class scores are decoded and class-aware NMS is applied. A dependency-free IoU association tracker creates per-camera temporary IDs. People and vehicles are counted; current traffic/minute is a new-track rate proxy, not calibrated line-crossing flow. A short track history supports a weak downward-motion + sustained horizontal-box fall indication, speed-based unusual-motion cue and 15-second stationary-object indication. The alerts carry evidence snapshots and remain pending.

One async task is assigned per camera, but model inference is serialized through one shared session to fit the measured hardware envelope. REST is used by the dashboard for periodic data refresh; FastAPI WebSocket updates are also implemented for clients.

## Research question and proposed contribution
**Research question:** Under a fixed CPU-time budget, can adaptive per-camera inference cadence plus temporal confirmation preserve event-level recall while reducing compute, without increasing detection delay or false alerts beyond a stated threshold?

**Proposed technical contribution:** Budgeted Camera-Local Temporal Evidence (BCLTE), defined in `research_review.md`. It connects per-camera compute allocation to temporal evidence accumulation, event latency and human verification, while explicitly avoiding cross-camera identity joins. This is a hypothesis, not a novelty claim. Adaptive cadence is not yet implemented; prior-art review and labelled evaluation remain pending.

## Evaluation plan
Runtime benchmark on four CC BY 4.0 sample clips is complete. It measures inference latency, FPS, process CPU and RSS across 320/416/640 FP32 and weight-only INT8. Because clips lack labels, detection/event accuracy metrics are unavailable. The next evaluation uses approved public benchmarks or controlled consented footage, scene-disjoint splits, event temporal annotations, at least three repeats, and event-level precision/recall/F1, false alarms per camera-hour, miss rate, event delay, FPS, CPU, GPU (where present) and peak memory. See `docs/evaluation.md`.

## Deliverables and roadmap
- Working prototype and tests: implemented; see `PROJECT_STATUS.md`.
- Research review, licensing notes and architecture: draft completed; dataset access still pending.
- Adaptive scheduler and labelled event evaluation: next research phase.
- Final academic report and defence slides: pending measured event experiments and supervisor review.

## Risk and ethics
False positives and missed events may be consequential. The prototype provides cues only; operators must verify. Any deployment needs privacy/security review, informed/legal authority, role controls, retention enforcement and an incident response policy. Public benchmark licences differ; no dataset is redistributed by this project. Demo footage is identified and attributed.
