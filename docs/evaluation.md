# Experimental Evaluation (Measured, Not Inferred)

## Test environment

- CPU-only sandbox: 2 logical CPU cores, Intel Xeon Processor 2.60 GHz reported by PyTorch, no GPU.
- Python 3.13.18, ONNX Runtime 1.32.0, OpenCV 4.11, YOLOv8n ONNX dynamic FP32 and weight-only INT8.
- Four bundled Intel sample videos. `benchmark.py --frames-per-clip 20` sampled the first 20 frames of each clip (80 input frames per model/resolution). These clips have **no ground-truth labels** in this project.
- 2 ORT intra-op threads, 1 inter-op thread; confidence threshold .32. Results are one measured run, not a multi-run confidence interval.

## Actual model benchmark

| Variant | Input | Frames | Model inference mean / p95 | End-to-end runner throughput* | Process CPU | Process RSS** |
|---|---:|---:|---:|---:|---:|---:|
| FP32 | 320×320 | 80 | 13.71 / 14.56 ms | 68.62 fps | 198.9% | 203.6 MB |
| FP32 | 416×416 | 80 | 24.07 / 28.76 ms | 39.35 fps | 198.7% | 237.5 MB |
| FP32 | 640×640 | 80 | 54.10 / 62.29 ms | 17.42 fps | 199.2% | 267.0 MB |
| Weight-only INT8 | 320×320 | 80 | 62.79 / 68.88 ms | 15.68 fps | 199.0% | 243.1 MB |
| Weight-only INT8 | 416×416 | 80 | 109.10 / 124.98 ms | 9.04 fps | 198.7% | 246.2 MB |
| Weight-only INT8 | 640×640 | 80 | 240.13 / 282.06 ms | 4.11 fps | 198.6% | 277.1 MB |

\* Runner throughput includes preprocessing and a single inference for each frame. It is not camera capture/network/display throughput. Process CPU percentages can reach ~200% because the process used both cores; system CPU sampled at 100% during these CPU-bound runs.  
\** RSS is process resident memory after each sequential run; ORT allocator/cache effects mean values are not isolated per-model peak allocations. Benchmark process grew from about 204 to 277 MB. Use a fresh process per variant for strict memory comparisons.

**Interpretation:** 320/416 FP32 is the suitable CPU path. Weight-only INT8 is smaller on disk (~3.2 MB vs ~12.7 MB), but was **4.6× slower at 320 px** on this specific CPU and had different unlabelled confidence outputs. Do not select INT8 based on model size alone. The model storage sizes are not accuracy metrics. Dynamic FP32 export is bit-exact with a static 640 export from the same checkpoint on one seeded random tensor: max absolute difference 0.0, mean absolute difference 0.0. Dynamic shape smoke tests passed at 320, 416 and 640 for both detection (outputs [1,84,anchors]) and pose ([1,56,anchors]).

A post-change live service smoke measurement used two active sample-file camera workers for 15 seconds: mean aggregate processed FPS 33.55 (range 32.1–35.7), mean system CPU utilisation 90.2%, and maximum observed API-process RSS 220.5 MB. Counts varied by source frame. This is one short run under the sandbox and is not a stable service-level or accuracy guarantee. Raw samples are in `data/evaluation/live_system_smoke.json`.

## Accuracy and event quality: not yet measured

The system has not been evaluated against annotated target-domain videos. Therefore no precision, recall, F1, mAP, false-positive rate, false-negative rate, event-level delay, fall sensitivity, abandoned-object sensitivity, or crowd-count MAE is reported here. Detection counts above threshold in the CSV are **unlabelled observations**, not true positives. The supplied clips are demonstrations, not a validation dataset.

The following protocol is required before claiming accuracy:

1. Obtain access/licence approval for UCSD, Avenue, ShanghaiTech and selected traffic/fall datasets; record source, terms and split hashes.
2. Use person/object boxes for detector mAP/precision/recall and tracking identity annotations for IDF1/HOTA where available.
3. Keep a camera/scene-disjoint test split; do not split adjacent frames across train/test.
4. For event modules, annotate event start/end, category and evidence window; report event-level precision/recall/F1, false alerts per camera-hour and detection delay.
5. Run at least three seeded repeats and bootstrap by camera/clip; report 95% intervals, threshold selection protocol and error examples.
6. Stratify by illumination, camera angle, occlusion/crowd, source resolution and hardware. Use held-out controlled videos rather than attempting to infer demographic attributes.
7. Measure end-to-end capture-to-alert latency, stale-frame age, FPS per camera, CPU per core, peak process and system RAM, and accelerator use (N/A for this machine).

## Ablation plan for BCLTE

| Variant | Purpose | Status |
|---|---|---|
| Fixed 416 px, no temporal confirmation | Per-frame baseline | Detector benchmark only; no event ground truth yet |
| Fixed 416 px + motion/persistence temporal cues | Isolate value/cost of temporal confirmation | Implemented heuristic; not evaluated on labeled events |
| Budgeted inference cadence + temporal confirmation | Test proposed adaptive scheduling | Not implemented |
| FP32 vs weight-only INT8 | Device-specific quantization trade-off | Runtime measured; detection accuracy comparison blocked by absent labels |

## Reproducibility artifacts

- `backend/tools/benchmark.py`
- `data/evaluation/model_benchmark.csv`
- `data/evaluation/model_benchmark.json`
- `backend/models/yolov8n.onnx`, `yolov8n.int8.onnx`, `yolov8n-pose.onnx`

Rerun from `backend/` with `python tools/benchmark.py --frames-per-clip 20`. Do not compare these numbers directly to paper-reported throughput on a V100 or a different inference pipeline.
