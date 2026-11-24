# Faculty Demonstration Script (6–8 minutes)

## Before the panel arrives

1. Start backend and frontend using the README. Keep the API on port 8000 and dashboard on 3000.
2. Confirm `/api/health` is `ok`. Overview shows the verified Chennai still-image embeds as `IMAGE REFRESH`; confirm last-check time and source credit. These are not continuous video and are not analyzed by the CV worker. No Indian continuous public video source is currently verified.
3. Confirm each source card distinguishes its last health check from the source image modification time; provider embeds may be unavailable or intermittently stale.
4. Do not use any unauthorised CCTV feed. Do not claim the sample videos are a labelled test set or the India image embeds are CV detections.

## Talk track and live actions

### 1. Problem and responsible scope (45 s)
“Conventional CCTV records footage but leaves operators to detect events manually. GOD'S EYE turns authorized video into object counts and observable temporal cues. It does not recognise faces or link identities across cameras, and it cannot determine criminal intent or dangerousness. Every alert remains pending until an operator reviews it; nothing automatically contacts emergency services.”

Point out the privacy notice and camera-local temporary tracking IDs.

### 2. Architecture and hardware trade-off (60 s)
Show Architecture in `docs/architecture.md`: independent async camera workers, one shared ONNX Runtime CPU session, NMS + temporary IoU tracking, temporal cue evaluation, FastAPI/SQLAlchemy and React/Recharts UI. Explain the small YOLOv8n selection: 2 CPU cores, ~1.9 GB RAM, no GPU. The optional pose export is not run in the main pipeline because another full model pass would compete for this CPU; no Pi or Jetson was tested.

### 3. India source registry and refresh status (90 s)
On Overview, point out the two Chennai OpenCCTV embeds, `IMAGE REFRESH` labels, coordinates, source attribution and last-check metadata. Explain that the provider embeds are refreshed stills, not continuous streams. The displayed image is supplied by the official third-party embed; GOD’S EYE checks the JPEG endpoint for health but does not store it or run YOLO on it. No Indian continuous public video source is currently verified, so people/vehicle detection counts and video FPS are shown as unavailable rather than zero or fabricated.

### 4. Alert/event workflow and temporal module (90 s)
Open Incidents. Camera-online messages are INFORMATIONAL. Warnings and possible falls are generated from simple observable temporal cues. Demonstrate the tested temporal state machine with:

```bash
cd backend && pytest -q tests/test_cv_engine.py::test_fall_cue_requires_temporal_sequence
```

The test feeds a synthetic sequence of person-box detections to the temporal state module: downward track displacement followed by a sustained horizontal box. It verifies an event after the persistence window. **This validates the state logic only; it is not a real video fall-recognition accuracy result.** The two current Indian feeds are still images and cannot produce video events. The Incidents page should be empty unless an authorized video source has actually generated a record; do not create a fake alert to demonstrate the workflow. Explain the Verify/Acknowledge/Dismiss controls from the existing UI or code, not as a current India-feed capability.

### 5. Analytics and configuration (60 s)
Open Analytics and explain that India image-refresh sources intentionally provide no detection metrics, event counts, or temporal charts; empty states are correct, not missing or zero-valued camera detections. If an authorized video source is separately configured, its genuine metrics appear there. In System Settings show that the existing backend validates/persists configuration. Avoid enabling INT8 for this CPU demonstration: the historical development benchmark found it slower, not faster.

### 6. Measured results and limitations (60 s)
Open `docs/evaluation.md` and the CSV. Report only these observed runtime results: FP32 inference averaged 13.71 ms at 320 px, 24.07 ms at 416 px, and 54.10 ms at 640 px on this CPU. INT8 was slower. State clearly that no labelled benchmark was run, so precision/recall/F1/mAP and fall detection accuracy are not available. Show the proposed research gap and BCLTE hypothesis in `docs/research_review.md` as proposed work—not a demonstrated novelty claim.

### 7. Close (30 s)
“The prototype demonstrates an end-to-end human-in-the-loop workflow. Its current claim is systems integration with measured resource trade-offs and auditable retention/verification—not validated detection accuracy. Next we will obtain dataset permissions, annotate held-out campus-like sequences, implement budgeted cadence and evaluate event-level false alarms and delay.”

## Troubleshooting

- If the backend is disconnected, restart the API from `backend/`; model loading takes a few seconds.
- If an Indian image-refresh source is unavailable, check its provider page and current image endpoint; backend health status retries automatically. Do not switch to a bundled clip as a fallback.
- For authorized local video experiments only, limit active sources and use `INFER_SIZE=320` in `backend/.env` if CPU is saturated. The public image-refresh feeds do not use the CV worker.
- If no temporal fall alert occurs, use the test command above and explain the lack of labelled fall footage; do not fabricate a live alarm or experimental result.
