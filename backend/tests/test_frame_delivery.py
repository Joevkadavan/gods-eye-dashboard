"""Integration check: real detector output and the image in the frame API stay paired."""
import base64
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from sqlalchemy import text

import main
from cv_engine import CameraState, YoloDetector, draw_overlay


def test_synchronized_frame_endpoint_pairs_real_sample_detection_with_its_jpeg(monkeypatch):
    video = Path(__file__).resolve().parents[2] / "data/media/person-bicycle-car-detection.mp4"
    model_path = Path(__file__).resolve().parents[1] / "models/yolov8n.onnx"
    cap = cv2.VideoCapture(str(video))
    detector = YoloDetector(model_path, imgsz=416, confidence=.32, threads=1)
    frame = detections = None
    latency = 0.0
    try:
        for _ in range(80):
            ok, candidate = cap.read()
            if not ok:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            found, latency = detector.infer(candidate)
            if found:
                frame, detections = candidate, found
                break
    finally:
        cap.release()
    assert frame is not None and detections

    now = datetime.now(timezone.utc).timestamp()
    metrics, _ = CameraState("frame-test").analyze(frame, detections, now, latency)
    serialized = [{"bbox": d.bbox, "label": d.label, "class_id": d.class_id,
                   "confidence": d.confidence, "track_id": d.track_id} for d in detections]
    timestamp = datetime.now(timezone.utc).isoformat()
    camera_id = "test-synchronized-frame"
    monkeypatch.setattr(main, "detector", detector)
    main.hub.latest[camera_id] = {"camera_id": camera_id, "timestamp": timestamp,
                                  "metrics": metrics, "detections": serialized}
    main.hub.frames[camera_id] = draw_overlay(frame, detections)
    main.hub.raw_frames[camera_id] = frame.copy()
    try:
        response = main.synchronized_frame(camera_id, overlay=True)
        data = response.body
        import json
        payload = json.loads(data)
        image = cv2.imdecode(np.frombuffer(base64.b64decode(payload["frame_base64"]), np.uint8), cv2.IMREAD_COLOR)
        assert response.headers["cache-control"] == "no-store"
        assert payload["timestamp"] == timestamp
        assert payload["detections"] == serialized
        assert payload["overlay"] is True
        assert image.shape[:2] == (metrics["frame_height"], metrics["frame_width"])
        assert payload["model_status"] == "LOADED"
        assert all(0 <= d["bbox"][0] <= image.shape[1] and 0 <= d["bbox"][2] <= image.shape[1]
                   and 0 <= d["bbox"][1] <= image.shape[0] and 0 <= d["bbox"][3] <= image.shape[0]
                   for d in payload["detections"])

        raw = main.synchronized_frame(camera_id, overlay=False)
        raw_payload = json.loads(raw.body)
        raw_image = cv2.imdecode(np.frombuffer(base64.b64decode(raw_payload["frame_base64"]), np.uint8), cv2.IMREAD_COLOR)
        assert raw_payload["timestamp"] == timestamp
        assert raw_payload["detections"] == serialized
        assert raw_payload["overlay"] is False
        assert raw_image.shape == image.shape
    finally:
        main.hub.latest.pop(camera_id, None)
        main.hub.frames.pop(camera_id, None)
        main.hub.raw_frames.pop(camera_id, None)
