# GOD'S EYE: A Human-Verified, Resource-Aware Video Analytics Prototype for Public-Space Monitoring

**Working academic manuscript — draft; not yet a final empirical paper**  
**Authors:** Capstone project team / VIT faculty and student authors to be completed  
**Date:** 24 November 2026

> This manuscript reports system and runtime experiments only. The bundled sample clips are not annotated ground truth; no detector or event-recognition accuracy is claimed. The proposed adaptive technical contribution is not yet implemented. Review, dataset permission, prior-art study and final experiment sections require further work before submission.

## Abstract

This paper describes GOD'S EYE, a local-first video analytics prototype that transforms authorized video feeds into object detections, temporary camera-local tracks, aggregate crowd and traffic indicators, and human-reviewable temporal event cues. The system couples a dynamically shaped YOLOv8n ONNX model with OpenCV, a shared CPU inference session, an asynchronous FastAPI service, SQLAlchemy persistence and a Next.js command-centre dashboard. It is designed around an explicitly constrained development target of two CPU cores, approximately 1.9 GB of RAM and no GPU. Temporal logic combines tracked vertical displacement with a sustained horizontal person bounding box as a weak possible-fall indication; stationary non-person objects and rapid image-plane movement are also surfaced as observable cues. Every alert starts pending and includes an evidence image for operator verification; the platform has no face recognition, identity linkage, criminal-intent inference or automatic emergency-service contact. On an unlabelled 80-frame sample-video benchmark, FP32 YOLO inference averaged 13.71 ms at 320×320, 24.07 ms at 416×416 and 54.10 ms at 640×640. Weight-only INT8 was slower on this CPU (62.79 ms mean at 320×320). A two-camera live smoke test achieved a mean aggregate processing rate of 33.55 fps while system CPU utilisation averaged 90.2%. These results describe runtime only; precision, recall, F1, mAP, false-alarm rates and event sensitivity remain unmeasured. We formulate Budgeted Camera-Local Temporal Evidence (BCLTE) as a falsifiable future research hypothesis: adapt per-camera inference cadence under a fixed CPU budget while measuring temporal event quality, freshness and delay. The present system is an engineering prototype and not suitable for unsupervised public-safety deployment.

**Keywords:** video analytics, edge inference, object detection, temporal event cues, human verification, privacy-aware design, ONNX Runtime

## 1. Introduction

Fixed cameras create large quantities of video, and manual continuous monitoring can be burdensome. Computer-vision systems can assist operators by identifying objects and summarising observable changes, but a single frame does not establish a temporally meaningful event. A person-shaped bounding box in a horizontal orientation, for example, is not sufficient evidence of a fall without temporal context; nor does crowd density alone establish danger. Practical monitoring also faces limited processing hardware, differing camera viewpoints, occlusion, storage constraints and privacy obligations.

GOD'S EYE is a demonstration prototype that connects object detection and temporary tracking to a central human-in-the-loop dashboard. Its purpose is not to automate policing or infer an individual's identity or intent. It provides limited event cues, time-stamped evidence and configurable local retention so an operator can decide whether a cue is relevant.

This paper makes three bounded contributions:

1. An end-to-end, locally runnable multi-camera prototype on a CPU-only development target, with one independent asynchronous capture worker per camera and a shared ONNX inference session.
2. A working alert lifecycle that associates a camera, category, timestamp, confidence, severity, evidence image and human verification state; stored metric samples support short historical analytics.
3. A measured resolution and weight-only quantisation comparison on the available CPU, together with a candid statement of what cannot yet be concluded without annotated evaluation data.

The paper also proposes BCLTE, a future adaptive-scheduling research direction. It is not claimed as a completed algorithm or novel result.

## 2. Problem statement and objectives

### 2.1 Problem statement

The engineering problem is to process multiple authorized video sources without making camera capture or the web dashboard block on model inference, surface potentially relevant observable events with temporal evidence, and bound retention and compute on a conventional computer. The research problem is to determine how inference budget allocation affects event-level recall, false alerts, latency and evidence freshness under a fixed CPU budget.

### 2.2 Objectives

- Detect COCO object classes in video frames and render bounding boxes, labels and confidence.
- Associate detections across adjacent frames with temporary camera-local IDs.
- Estimate people and vehicle counts, configurable crowd-count alerts and simple traffic indicators.
- Implement at least one temporally qualified event cue rather than single-frame event classification.
- Persist events and evidence while enforcing human verification and finite retention.
- Provide a dashboard with camera management, live view, event management, analytics and settings.
- Measure inference latency, throughput, CPU and memory across detector resolution and INT8/FP32 variants.
- Establish an authorized dataset and event annotation plan before reporting accuracy.

## 3. Related work

### 3.1 Video anomaly and temporal modelling

Mahadevan et al. modelled appearance and motion with Mixtures of Dynamic Textures and evaluated on UCSD Ped1/Ped2 crowded walkways. Their paper reports a 25% equal-error rate for MDT on each subset in its frame-level comparison [1]. The result is tied to small, fixed-camera walkway scenes and should not be read as modern multi-camera operational accuracy.

Lu et al. proposed sparse combination learning for abnormal event detection and reported average processing around 140–150 frames/s in MATLAB on an ordinary desktop [2]. This result demonstrates that runtime can be a first-class design target, but feature generation, hardware and end-to-end service load differ from this prototype. Xu et al.'s Appearance and Motion DeepNet learned appearance/motion features with double fusion and one-class normality modelling. Published benchmark summaries report frame AUC of 92.1% on UCSD Ped1 and 90.8% on Ped2 [3]. Spatiotemporal autoencoder approaches likewise model normal video cubes and score reconstruction regularity [4]. These methods show temporal modelling precedents while also illustrating why scene-specific benchmarks and frame-level scores do not directly answer alert-level questions.

Recent surveys organise video anomaly detection approaches across supervised, weakly supervised, reconstruction-based and temporal methods [5]. A separate privacy-preserving survey describes non-identifiable visual abstractions and intermediate modalities such as skeletons and optical flow, while noting their differing compute and coverage trade-offs [6]. Such representations may reduce exposure to raw appearance but do not automatically eliminate privacy risks.

### 3.2 Tracking and crowded-scene detection

ByteTrack associates low-confidence detections with existing tracklets to recover objects that may be occluded. On MOT17 test, the authors report 80.3 MOTA, 77.3 IDF1, 63.1 HOTA and approximately 29.6 fps on an NVIDIA V100 [7]. Those results use a different detector, tracker and accelerator than the CPU-based IoU tracker in GOD'S EYE. The present implementation is intentionally simpler, camera-local and temporary; it is not expected to match ByteTrack under occlusion.

CrowdHuman provides full-body, visible-region and head bounding boxes for crowded human detection and reports 470,000 person instances across training and validation [8]. It supports dense person detection research but does not provide temporal crowd-flow or fall labels for this project. Licence and redistribution conditions must be respected.

### 3.3 Research gap

Prior benchmarks demonstrate frame-level anomaly scoring, tracking performance or algorithm throughput, but these do not by themselves measure camera-hour alert burden, event delay, stale-frame age or operator review workload on a CPU-limited multi-camera system. Moreover, accuracy, privacy/retention and resource allocation are often evaluated separately. This motivates a testable deployment question, not an assertion that no related work exists: **under a fixed CPU-time budget, can adaptive inference scheduling plus temporal confirmation maintain event-level recall and acceptable alert delay while reducing unnecessary computation?**

The proposed response is Budgeted Camera-Local Temporal Evidence (BCLTE): a bounded per-camera inference scheduler, camera-local observable state and temporally qualified event evidence, with performance measured by event-level quality, false alerts per camera-hour, delay, freshness, CPU and memory. The adaptive scheduler is not present in the current prototype; BCLTE remains a research hypothesis pending prior-art review and evaluation.

## 4. System design and methodology

### 4.1 Runtime and model

The available target is a CPU-only environment with two logical cores, approximately 1.9 GB RAM and no GPU. A COCO-pretrained YOLOv8n checkpoint was exported to a dynamic-shape ONNX graph and run through ONNX Runtime's CPU execution provider. Dynamic spatial input supports dimensions from 320 to 640 pixels in multiples of 32. Preprocessing uses aspect-preserving letterboxing; class scores are decoded from the model output and class-aware non-maximum suppression filters overlapping boxes.

The pose variant was also exported and its dynamic shapes were smoke-tested, but it is not invoked in the default video loop. A second neural inference pass would compete with the two-core budget and has not been justified by a validated fall evaluation. PyTorch and Ultralytics are build-time export dependencies, not server runtime dependencies.

### 4.2 Tracking and analytics

Each camera has an independent IoU association tracker. Track IDs are ephemeral, local to a camera and not joined across cameras. People counts update per processed frame; maximum observed people count resets with the camera processing session. Crowd status is determined by a configurable count threshold; density is people per image megapixel and is not perspective calibrated. A sudden count increase can produce a warning but high count is not inherently classified as dangerous.

Vehicle categories are derived from COCO object labels. The current rolling vehicles-per-minute indicator counts newly appearing vehicle tracks, which can be affected by track fragmentation and is therefore a traffic-flow proxy rather than a calibrated line-crossing measure. Category distribution is based on current processed feed detections.

### 4.3 Temporal event cues

The possible-fall cue uses at least three components: a tracked person's downward center displacement, a horizontal bounding-box geometry, and persistence for 2.5 seconds. The state machine is unit-tested using a synthetic detection sequence. This tests the temporal state transition but does not establish visual detection sensitivity or event accuracy. The cue is not a pose classifier, medical diagnosis or reliable emergency detector.

A non-person, non-vehicle COCO object may generate a stationary-object warning after a configurable duration (15 seconds by default) while continuously tracked. It does not infer threat or ownership. Rapid image-plane track displacement creates an unusual-motion warning; it does not infer intent or dangerousness. Event deduplication limits repeated alerts per category and camera.

### 4.4 Multi-camera and persistence architecture

An asynchronous task per camera reads frames using OpenCV, performs inference through a shared session protected by an async lock and updates its own tracker. This avoids allocating a model session for each camera. The backend emits REST responses and WebSocket messages. The current dashboard uses same-origin REST polling every 2.5 seconds, avoiding browser-to-localhost dependencies in the preview environment.

SQLAlchemy persists cameras, events and ten-second metric samples. SQLite is the default local store; PostgreSQL is available in Docker Compose. Evidence snapshots and uploaded files are expired by a periodic retention worker, with a 24-hour default. The source video is not stored as a continuous recording. Camera status and operator actions are visible through the dashboard. The prototype has no authentication or role-based access control and must not be exposed as a public service.

## 5. Implementation

The project is divided into `backend/cv_engine.py` for model preprocessing, NMS, tracking and temporal cues; `backend/main.py` for FastAPI, camera workers, event routing, retention and configuration; `backend/db.py` for SQLAlchemy entities; and `frontend/app/` for the React dashboard. `backend/tools/export_models.py` reproducibly exports the dynamic ONNX model. `backend/tools/benchmark.py` measures inference and resource use, while `backend/tools/measure_live.py` records system-level observations. Five automated tests cover IoU, track ID continuity, sample-video person detection, temporal fall-state logic and duration-based stationary-object cues.

The dashboard contains Overview, Live Monitoring, Incidents, Analytics, Cameras and System Settings pages. Event states include `PENDING`, `ACKNOWLEDGED`, `VERIFIED` and `DISMISSED`. No action sends alerts to external authorities. Environment variables and validated runtime settings configure model, resolution, thresholds, maximum camera count and retention.

## 6. Experimental setup

### 6.1 Hardware and software

The benchmark ran on the two-core, CPU-only sandbox. Python 3.13.18, ONNX Runtime 1.32.0 and OpenCV 4.11 were used. Both FP32 and dynamic weight-only INT8 models used two intra-op threads and one inter-op thread. The four bundled Intel sample clips are licensed CC BY 4.0 according to the source repository and are used as demonstration footage only [9]. They are not annotated by this project.

### 6.2 Inference benchmark

The benchmark sampled the first 20 frames of each of four videos (80 frames per setting), warmed each session with three runs, and tested 320, 416 and 640 input sizes. Throughput includes preprocessing and model execution, but not video capture, network transport or browser rendering. CPU and process RSS were sampled; GPU use is not applicable. The observed run is not repeated across seeds and does not provide a confidence interval.

### 6.3 Live two-camera smoke measurement

Two sample-file camera workers ran simultaneously for 15 seconds. The API was sampled once per second and aggregate FPS, CPU use and process RSS were recorded. This test confirms that two asynchronous feed workers and the dashboard API operate concurrently; it is not a scalability or accuracy test.

## 7. Results and discussion

### 7.1 Inference speed/resource results

| Model | Input | Frames | Mean inference (ms) | P95 inference (ms) | Runner throughput (fps) | Process CPU | Process RSS (MB) |
|---|---:|---:|---:|---:|---:|---:|---:|
| FP32 | 320 | 80 | 13.71 | 14.56 | 68.62 | 198.9% | 203.6 |
| FP32 | 416 | 80 | 24.07 | 28.76 | 39.35 | 198.7% | 237.5 |
| FP32 | 640 | 80 | 54.10 | 62.29 | 17.42 | 199.2% | 267.0 |
| Weight-only INT8 | 320 | 80 | 62.79 | 68.88 | 15.68 | 199.0% | 243.1 |
| Weight-only INT8 | 416 | 80 | 109.10 | 124.98 | 9.04 | 198.7% | 246.2 |
| Weight-only INT8 | 640 | 80 | 240.13 | 282.06 | 4.11 | 198.6% | 277.1 |

The process CPU percentage can approach 200% because both logical CPU cores were utilised. System CPU sampled at 100% during the isolated CPU-bound benchmark. RSS figures are sequential post-run process readings and may include ONNX Runtime allocator/cache effects; they are not isolated per-model peak memory. The INT8 model file is about 3.2 MB compared with about 12.7 MB for FP32, but INT8 was approximately 4.6 times slower at 320 pixels on this CPU. The result is device-specific and demonstrates that model-size reduction alone is not a sufficient edge deployment criterion.

A static 640 export and dynamic 640 export from the same checkpoint produced max and mean absolute difference 0.0 on a seeded input. Both detection and pose ONNX graphs ran at 320, 416 and 640 input sizes. This is an export consistency check, not an accuracy evaluation.

### 7.2 Live two-camera result

For the 15-second live measurement, two feeds remained active. Mean aggregate processed throughput was 33.55 fps (range 32.1–35.7), mean system CPU utilisation was 90.2%, and the maximum observed API-process RSS was 220.5 MB. The current FPS measurement is derived from per-camera processed-frame intervals and summed in the overview; it does not represent video source frame rate or display refresh rate. CPU was near saturation, so more active cameras should not be assumed to scale linearly.

### 7.3 Accuracy and event detection

Precision, recall, F1, mAP, false-positive rate, false-negative rate, crowd-count MAE, fall sensitivity, event precision/recall and alert delay are not reported. The sample clips lack ground-truth annotation, and the synthetic fall test covers only a deterministic state transition. Consequently, claims of successful fall recognition, anomaly accuracy or reliable emergency detection would be unsupported. The system has only been sanity-checked for a person detection on a specific sample frame and visual overlay on live sample feeds.

## 8. Privacy, safety and dataset governance

The implementation avoids face recognition, cross-camera re-identification, biometric/demographic inference and criminality or dangerousness predictions. Tracking IDs are short-lived and camera-local. Crowd density is a count statistic, not a danger judgement. Event cues require human verification and the system never contacts emergency services. Video evidence and uploaded test videos expire under a configurable retention policy; no continuous archive is created by the application.

Academic dataset access is not yet complete. CrowdHuman terms restrict image use to non-commercial research/education and prohibit image redistribution [8]. MOT17 benchmark licensing and official registration conditions must be checked. The UCSD and Avenue official resources should be consulted for current terms; third-party mirrors do not establish permission. ShanghaiTech campus dataset terms vary across mirrors and must be verified at primary source. UCF-Crime and VIRAT require careful research-use/access review; VIRAT requires each user to sign an agreement and restricts redistribution [10]. No such datasets were downloaded in this prototype. Intel sample media are attributed under CC BY 4.0 [9].

## 9. Limitations

- No labelled target-domain dataset or accuracy metrics.
- The possible-fall algorithm is a bounding-box/motion heuristic, not pose-based or learned action recognition.
- IoU association is vulnerable to occlusion, detector misses and ID switches.
- Crowd density is not calibrated for perspective; crowd alerts use absolute count.
- Vehicle flow uses new track detections, not line-crossing calibration; collision detection is absent.
- No adaptive cadence, multi-camera event correlation, GPU/TensorRT, Raspberry Pi or Jetson test.
- No API authentication, RBAC, TLS or production operational hardening.
- The two-feed run approaches CPU capacity; service throughput should not be extrapolated to more cameras.
- Benchmark metrics are a single unlabelled run and no repeated-measures intervals are available.

## 10. Conclusion and future work

GOD'S EYE demonstrates a connected path from authorized video files to dynamic ONNX object detections, temporary tracking, temporal heuristic cues, persistent human-review events and a web dashboard. The tested CPU trade-off favours FP32 at 320–416 pixels; weight-only INT8 was slower on the available host. A short two-camera smoke test achieved about 33.6 aggregate processed fps but consumed most of the system CPU.

This paper's central empirical conclusion is limited: the end-to-end prototype runs and its runtime characteristics are measured. Its detection accuracy and event usefulness are not established. Future work should first obtain dataset permissions, create camera/scene-disjoint event labels and evaluate false alerts, misses and delay. Only then should the BCLTE scheduler be implemented and compared against fixed-rate baselines. Additional work includes pose-assisted temporal fall experiments, calibrated traffic line crossing, tracker robustness, edge hardware tests and security/role controls before any real deployment.

## References

[1] V. Mahadevan, W. Li, V. Bhalodia, and N. Vasconcelos, “Anomaly Detection in Crowded Scenes,” *IEEE Conference on Computer Vision and Pattern Recognition*, 2010, pp. 1975–1981. [Paper PDF](http://www.svcl.ucsd.edu/publications/conference/2010/cvpr2010/cvpr_anomaly_2010.pdf).

[2] C. Lu, J. Shi, and J. Jia, “Abnormal Event Detection at 150 FPS in MATLAB,” *IEEE International Conference on Computer Vision*, 2013, pp. 2720–2727. [doi:10.1109/ICCV.2013.338](https://doi.org/10.1109/ICCV.2013.338).

[3] D. Xu, E. Ricci, Y. Yan, J. Song, and N. Sebe, “Learning Deep Representations of Appearance and Motion for Anomalous Event Detection,” *British Machine Vision Conference*, 2015. [arXiv:1510.01553](https://arxiv.org/abs/1510.01553); benchmark values referenced from the review table at [arXiv:2409.05383](https://arxiv.org/html/2409.05383v1).

[4] C. Lu, J. Shi, and J. Jia, “Abnormal Event Detection in Videos using Spatiotemporal Autoencoder,” *IEEE International Conference on Acoustics, Speech and Signal Processing*, 2017. [arXiv:1701.01546](https://arxiv.org/abs/1701.01546).

[5] “Networking Systems for Video Anomaly Detection: A Tutorial and Survey,” arXiv:2405.10347, 2024. [arXiv](https://arxiv.org/abs/2405.10347).

[6] “Privacy-Preserving Video Anomaly Detection: A Survey,” arXiv:2411.14565, 2024. [arXiv](https://arxiv.org/abs/2411.14565).

[7] Y. Zhang et al., “ByteTrack: Multi-Object Tracking by Associating Every Detection Box,” *European Conference on Computer Vision*, 2022. [doi:10.1007/978-3-031-20047-2_1](https://doi.org/10.1007/978-3-031-20047-2_1).

[8] S. Shao et al., “CrowdHuman: A Benchmark for Detecting Human in a Crowd,” arXiv:1805.00123, 2018. [Paper](https://arxiv.org/abs/1805.00123); dataset terms at [author-hosted data page](https://huggingface.co/datasets/sshao0516/CrowdHuman).

[9] Intel IoT DevKit, “Sample Videos,” CC BY 4.0. [Repository](https://github.com/intel-iot-devkit/sample-videos) · [license](https://github.com/intel-iot-devkit/sample-videos/blob/master/LICENSE).

[10] Kitware, “VIRAT Video Dataset Usage Agreement,” 2011. [Agreement PDF](https://viratdata.org/resources/VIRAT-Video-Data-Set-Protection-Agreement-1-4-11.pdf).
