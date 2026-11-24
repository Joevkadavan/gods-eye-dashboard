"""CPU-first, ONNX Runtime vision engine for GOD'S EYE.

All video is processed transiently. This module emits detections, derived
statistics and event evidence images; it does not identify people.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import logging
import time
import uuid

import cv2
import numpy as np
import onnxruntime as ort

log = logging.getLogger("godseye.cv")
COCO = ["person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"]
VEHICLE_IDS = {2, 3, 5, 7}


def iou(a: np.ndarray, b: np.ndarray) -> float:
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0., x2-x1) * max(0., y2-y1)
    area_a = max(0., a[2]-a[0]) * max(0., a[3]-a[1])
    area_b = max(0., b[2]-b[0]) * max(0., b[3]-b[1])
    return inter / max(area_a + area_b - inter, 1e-8)


@dataclass
class Detection:
    bbox: list[float]
    class_id: int
    label: str
    confidence: float
    track_id: int | None = None


@dataclass
class Track:
    track_id: int
    bbox: np.ndarray
    class_id: int
    missed: int = 0
    age: int = 1
    stationary_since: float = field(default_factory=time.time)
    center_history: list[tuple[float, float, float]] = field(default_factory=list)


class IoUTracker:
    """Small dependency-free SORT-like tracker (IoU association, TTL).

    IDs are ephemeral, camera-local session IDs, not identities.
    """
    def __init__(self, max_missed: int = 12, match_iou: float = .25):
        self.max_missed, self.match_iou = max_missed, match_iou
        self.tracks: dict[int, Track] = {}
        self.next_id = 1

    def update(self, detections: list[Detection], now: float) -> list[Detection]:
        unmatched = set(self.tracks)
        candidates = sorted(((iou(t.bbox, np.asarray(d.bbox)), tid, j)
                             for tid, t in self.tracks.items()
                             for j, d in enumerate(detections) if t.class_id == d.class_id), reverse=True)
        used_det: set[int] = set()
        for score, tid, j in candidates:
            if score < self.match_iou or tid not in unmatched or j in used_det:
                continue
            track, det = self.tracks[tid], detections[j]
            old_center = ((track.bbox[0]+track.bbox[2])/2, (track.bbox[1]+track.bbox[3])/2)
            new = np.asarray(det.bbox, dtype=np.float32)
            new_center = ((new[0]+new[2])/2, (new[1]+new[3])/2)
            if np.linalg.norm(np.subtract(old_center, new_center)) > 8:
                track.stationary_since = now
            track.bbox, track.class_id, track.missed = new, det.class_id, 0
            track.age += 1
            track.center_history.append((now, *new_center))
            track.center_history = track.center_history[-30:]
            det.track_id = tid
            unmatched.remove(tid); used_det.add(j)
        for tid in list(unmatched):
            self.tracks[tid].missed += 1
            if self.tracks[tid].missed > self.max_missed:
                del self.tracks[tid]
        for j, det in enumerate(detections):
            if j in used_det: continue
            tid = self.next_id; self.next_id += 1
            box = np.asarray(det.bbox, dtype=np.float32)
            tr = Track(tid, box, det.class_id)
            tr.center_history = [(now, (box[0]+box[2])/2, (box[1]+box[3])/2)]
            self.tracks[tid] = tr
            det.track_id = tid
        return detections


class YoloDetector:
    def __init__(self, model_path: str | Path, imgsz: int = 416, confidence: float = .32, iou_threshold: float = .45, threads: int = 2):
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = max(1, threads)
        opts.inter_op_num_threads = 1
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.session = ort.InferenceSession(str(model_path), sess_options=opts, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        self.imgsz, self.confidence, self.iou_threshold = imgsz, confidence, iou_threshold
        log.info("loaded ONNX model %s input=%s", model_path, self.session.get_inputs()[0].shape)

    def infer(self, frame: np.ndarray) -> tuple[list[Detection], float]:
        h, w = frame.shape[:2]
        scale = min(self.imgsz / w, self.imgsz / h)
        nw, nh = int(round(w * scale)), int(round(h * scale))
        resized = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_LINEAR)
        canvas = np.full((self.imgsz, self.imgsz, 3), 114, dtype=np.uint8)
        px, py = (self.imgsz - nw) // 2, (self.imgsz - nh) // 2
        canvas[py:py+nh, px:px+nw] = resized
        blob = cv2.dnn.blobFromImage(canvas, 1 / 255., (self.imgsz, self.imgsz), swapRB=True)
        start = time.perf_counter()
        output = self.session.run(None, {self.input_name: blob})[0][0]
        latency = (time.perf_counter() - start) * 1000
        rows = output.T
        scores = rows[:, 4:]
        cls = scores.argmax(axis=1)
        conf = scores[np.arange(len(rows)), cls]
        valid = np.flatnonzero(conf >= self.confidence)
        if not len(valid): return [], latency
        xywh = rows[valid, :4]
        boxes = np.empty_like(xywh)
        boxes[:, 0] = xywh[:, 0] - xywh[:, 2] / 2
        boxes[:, 1] = xywh[:, 1] - xywh[:, 3] / 2
        boxes[:, 2] = xywh[:, 0] + xywh[:, 2] / 2
        boxes[:, 3] = xywh[:, 1] + xywh[:, 3] / 2
        boxes[:, [0, 2]] = (boxes[:, [0, 2]] - px) / scale
        boxes[:, [1, 3]] = (boxes[:, [1, 3]] - py) / scale
        boxes[:, [0, 2]] = boxes[:, [0, 2]].clip(0, w)
        boxes[:, [1, 3]] = boxes[:, [1, 3]].clip(0, h)
        # Class-aware greedy NMS, deliberately implemented locally to avoid
        # OpenCV's version-dependent multi-class NMSBoxes behaviour.
        kept: list[int] = []
        for ci in np.unique(cls[valid]):
            inds = [k for k in range(len(valid)) if cls[valid[k]] == ci]
            inds.sort(key=lambda k: float(conf[valid[k]]), reverse=True)
            while inds:
                best = inds.pop(0); kept.append(best)
                inds = [j for j in inds if iou(boxes[best], boxes[j]) <= self.iou_threshold]
        return [Detection(bbox=boxes[k].astype(float).tolist(), class_id=int(cls[valid[k]]),
                           label=COCO[int(cls[valid[k]])], confidence=float(conf[valid[k]])) for k in kept], latency


@dataclass
class CameraState:
    camera_id: str
    tracker: IoUTracker = field(default_factory=IoUTracker)
    previous_people: int = 0
    max_people: int = 0
    fps: float = 0.
    total_frames: int = 0
    vehicle_crossings: int = 0
    _last_time: float = field(default_factory=time.time)
    _last_counts: list[tuple[float, int, int]] = field(default_factory=list)
    _vehicle_entries: list[float] = field(default_factory=list)
    _fall_candidate: dict[int, tuple[float, float]] = field(default_factory=dict)

    def analyze(self, frame: np.ndarray, detections: list[Detection], now: float, latency_ms: float, crowd_warning_count: int = 15, stationary_seconds: int = 15) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        detections = self.tracker.update(detections, now)
        people = [d for d in detections if d.class_id == 0]
        vehicles = [d for d in detections if d.class_id in VEHICLE_IDS]
        # Count newly appearing vehicle tracks once (a detection-flow proxy),
        # not every visible vehicle in every processed frame.
        self._vehicle_entries.extend(now for d in vehicles if d.track_id in self.tracker.tracks and self.tracker.tracks[d.track_id].age == 1)
        self._vehicle_entries = [t for t in self._vehicle_entries if now - t <= 60]
        self.max_people = max(self.max_people, len(people))
        dt = max(now - self._last_time, 1e-3)
        self.fps = .8 * self.fps + .2 * (1 / dt) if self.fps else 1 / dt
        self._last_time = now; self.total_frames += 1
        self._last_counts.append((now, len(people), len(vehicles)))
        self._last_counts = [x for x in self._last_counts if now - x[0] <= 60]
        events: list[dict[str, Any]] = []

        # Crowd thresholds are camera-relative, configurable at API-level later.
        h, w = frame.shape[:2]
        density = len(people) / max((w*h) / 1_000_000, .01)
        crowd_level = "HIGH" if len(people) >= crowd_warning_count else "MODERATE" if len(people) >= max(2, crowd_warning_count // 2) else "LOW"
        if len(people) >= crowd_warning_count and len(people) >= self.previous_people + max(3, crowd_warning_count // 3):
            events.append({"category": "CROWDING", "severity": "WARNING", "confidence": .7,
                           "description": f"People count increased to {len(people)} in one processed frame; density {density:.1f}/MP."})
        self.previous_people = len(people)

        # Temporal fall proxy: sudden downward centre-of-box movement followed
        # by a horizontal person box sustained for 2.5 s. This is a weak
        # motion/posture cue, not a trained action classifier or medical claim.
        for d in people:
            x1,y1,x2,y2=d.bbox; bw,bh=x2-x1,y2-y1
            tid=d.track_id
            tr=self.tracker.tracks.get(tid) if tid is not None else None
            hist=tr.center_history if tr else []
            downward=False
            if len(hist)>=3:
                dtv=max(hist[-1][0]-hist[-3][0],1e-3)
                downward=(hist[-1][2]-hist[-3][2])/dtv > h*.22
            horizontal=bw > bh*1.12 and bw > 20 and d.confidence >= .48
            if horizontal and (downward or tid in self._fall_candidate):
                start, _ = self._fall_candidate.get(tid, (now, now))
                self._fall_candidate[tid] = (start, now)
                if now-start>=2.5 and now-start<2.8:
                    events.append({"category":"POSSIBLE_FALL", "severity":"CRITICAL", "confidence":round(min(.82,d.confidence*.75),3),
                                   "description":"Temporal cue: rapid downward track displacement followed by a sustained horizontal person-box posture for 2.5 s. Weak indication only; human verification required."})
            else:
                self._fall_candidate.pop(tid,None)

        # Potential abandoned object: non-person, non-vehicle track persists
        # (visible) and remains stationary for configurable 15 s.
        for tr in list(self.tracker.tracks.values()):
            if tr.class_id in {0, *VEHICLE_IDS}: continue
            if now - tr.stationary_since >= stationary_seconds and (now - tr.stationary_since) < stationary_seconds + .5:
                events.append({"category":"STATIONARY_OBJECT", "severity":"WARNING", "confidence":.6,
                               "description":f"Tracked {COCO[tr.class_id]} remained stationary for about {stationary_seconds} seconds. Not a threat classification; verify context."})

        # Observable anomaly: fast track displacement over the last 3 observations.
        for tr in self.tracker.tracks.values():
            hist=tr.center_history
            if tr.class_id == 0 and len(hist)>=3:
                dtv=max(hist[-1][0]-hist[-3][0],1e-3)
                speed_px_s=np.hypot(hist[-1][1]-hist[-3][1],hist[-1][2]-hist[-3][2])/dtv
                if speed_px_s > max(w,h)*.9 and (now - hist[-1][0]) < .5:
                    events.append({"category":"UNUSUAL_MOTION", "severity":"WARNING", "confidence":.55,
                                   "description":"Rapid image-plane movement detected; this is an observable-motion cue, not intent or dangerousness."})
                    # reset recent history so this is not emitted every frame
                    tr.center_history = hist[-1:]

        counts_60 = [x for x in self._last_counts if now - x[0] <= 60]
        metrics = {"people_count":len(people), "max_people":self.max_people,
                   "vehicle_count":len(vehicles), "crowd_density_per_megapixel":round(density,2),
                   "crowd_level":crowd_level, "fps":round(self.fps,1), "inference_ms":round(latency_ms,1),
                   "vehicles_per_minute":len(self._vehicle_entries), "frame_width":w, "frame_height":h}
        return metrics, events


def draw_overlay(frame: np.ndarray, detections: list[Detection]) -> np.ndarray:
    out=frame.copy()
    for d in detections:
        x1,y1,x2,y2=map(int,d.bbox)
        color=(48,210,130) if d.class_id==0 else (255,168,55)
        cv2.rectangle(out,(x1,y1),(x2,y2),color,2)
        label=f"{d.label} #{d.track_id} {d.confidence:.2f}"
        cv2.rectangle(out,(x1,max(0,y1-21)),(min(out.shape[1],x1+len(label)*8),y1),color,-1)
        cv2.putText(out,label,(x1+3,max(12,y1-6)),cv2.FONT_HERSHEY_SIMPLEX,.48,(10,18,24),1,cv2.LINE_AA)
    return out
