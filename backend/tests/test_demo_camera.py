from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import cv2
import pytest

import main
from cv_engine import YoloDetector


def test_packaged_indian_demo_is_decodable_and_real_detector_sees_road_objects():
    video = main.INDIAN_DEMO_FILE
    assert video.is_file() and video.stat().st_size > 1_000_000
    cap = cv2.VideoCapture(str(video))
    assert cap.isOpened()
    try:
        ok, frame = cap.read()
        assert ok and frame.shape[:2] == (1080, 1920)
    finally:
        cap.release()
    model = Path(__file__).resolve().parents[1] / "models/yolov8n.onnx"
    detector = YoloDetector(model, imgsz=416, confidence=.32, threads=1)
    detections, latency = detector.infer(frame)
    labels = {item.label for item in detections}
    assert "person" in labels and "car" in labels
    assert latency > 0
    assert all(0 <= d.bbox[0] <= frame.shape[1] and 0 <= d.bbox[2] <= frame.shape[1]
               and 0 <= d.bbox[1] <= frame.shape[0] and 0 <= d.bbox[3] <= frame.shape[0]
               for d in detections)
    assert "Pexels" in main.INDIAN_DEMO_ATTRIBUTION and "city not verified" in main.INDIAN_DEMO_ATTRIBUTION


def test_prerecorded_playback_pause_resume_and_replay_controls(monkeypatch):
    camera = SimpleNamespace(source_type="file", feed_kind="demo")
    db = MagicMock()
    db.get.return_value = camera
    monkeypatch.setattr(main, "SessionLocal", lambda: db)
    monkeypatch.setitem(main.demo_controls, "playback-test", {"paused": False, "position_ms": 700, "duration_ms": 1000})
    monkeypatch.setitem(main.hub.latest, "playback-test", {"timestamp": "old"})
    monkeypatch.setitem(main.hub.frames, "playback-test", object())
    try:
        paused = main.control_playback("playback-test", main.PlaybackIn(action="pause"))
        assert paused["paused"] is True
        resumed = main.control_playback("playback-test", main.PlaybackIn(action="play"))
        assert resumed["paused"] is False
        replay = main.control_playback("playback-test", main.PlaybackIn(action="replay"))
        assert replay["paused"] is False
        assert main.demo_controls["playback-test"]["seek_to_ms"] == 0.0
        assert "playback-test" not in main.hub.latest and "playback-test" not in main.hub.frames
    finally:
        main.demo_controls.pop("playback-test", None)


def test_playback_controls_reject_non_demo_sources(monkeypatch):
    camera = SimpleNamespace(source_type="rtsp", feed_kind="video")
    db = MagicMock()
    db.get.return_value = camera
    monkeypatch.setattr(main, "SessionLocal", lambda: db)
    with pytest.raises(main.HTTPException) as exc:
        main.control_playback("stream-test", main.PlaybackIn(action="pause"))
    assert exc.value.status_code == 400


def test_demo_video_route_is_inline_and_restricted_to_the_packaged_demo():
    response = main.prerecorded_video(main.INDIAN_DEMO_ID)
    assert response.media_type == "video/mp4"
    assert Path(response.path).resolve() == main.INDIAN_DEMO_FILE.resolve()
    assert response.headers["content-disposition"].startswith("inline")
    with pytest.raises(main.HTTPException) as exc:
        main.prerecorded_video("not-the-demo")
    assert exc.value.status_code == 404
