from datetime import datetime, timezone
from types import SimpleNamespace

import main


def event(timestamp, category="CROWD_DENSITY", severity="WARNING", status="PENDING"):
    return SimpleNamespace(timestamp=timestamp, category=category, severity=severity, verification_status=status)


def test_pending_review_counts_exclude_informational_and_demo_lifecycle_rows():
    assert main.is_review_alert(event(datetime.now(timezone.utc)))
    assert not main.is_review_alert(event(datetime.now(timezone.utc), severity="INFORMATIONAL"))
    assert not main.is_review_alert(event(datetime.now(timezone.utc), category="DEMO_PLAYBACK_STARTED", severity="WARNING"))
    assert not main.is_review_alert(event(datetime.now(timezone.utc), status="ACKNOWLEDGED"))


def test_event_frequency_is_actual_hourly_count_without_empty_buckets():
    events = [
        event(datetime(2026, 11, 24, 9, 2, tzinfo=timezone.utc)),
        event(datetime(2026, 11, 24, 9, 58, tzinfo=timezone.utc)),
        event(datetime(2026, 11, 24, 11, 1, tzinfo=timezone.utc)),
    ]
    actual = main.hourly_event_frequency(events)
    assert actual == [
        {"timestamp": "2026-11-24T09:00:00+00:00", "count": 2},
        {"timestamp": "2026-11-24T11:00:00+00:00", "count": 1},
    ]
    assert all(row["count"] > 0 for row in actual)


def test_hourly_frequency_normalizes_legacy_naive_utc_timestamps():
    actual = main.hourly_event_frequency([event(datetime(2026, 11, 24, 9, 37))])
    assert actual == [{"timestamp": "2026-11-24T09:00:00+00:00", "count": 1}]


def test_analytics_preserves_event_rows_and_adds_actual_bucket_field(monkeypatch):
    from unittest.mock import MagicMock
    first = event(datetime(2026, 11, 24, 9, 2, tzinfo=timezone.utc))
    first.id, first.camera_id, first.confidence, first.description = "e1", "c1", .8, "cue"
    second = event(datetime(2026, 11, 24, 9, 45, tzinfo=timezone.utc))
    second.id, second.camera_id, second.confidence, second.description = "e2", "c1", .9, "cue"
    db = MagicMock()
    db.scalars.side_effect = [[second, first], []]
    monkeypatch.setattr(main, "SessionLocal", lambda: db)
    monkeypatch.setattr(main.hub, "latest", {})
    result = main.analytics()
    assert result["event_frequency"] == [
        {"timestamp": first.timestamp.isoformat(), "category": first.category, "severity": first.severity},
        {"timestamp": second.timestamp.isoformat(), "category": second.category, "severity": second.severity},
    ]
    assert result["event_frequency_buckets"] == [{"timestamp": "2026-11-24T09:00:00+00:00", "count": 2}]


def test_analytics_normalizes_naive_retained_metric_timestamps_to_utc(monkeypatch):
    from unittest.mock import MagicMock
    sample = SimpleNamespace(
        timestamp=datetime(2026, 11, 24, 9, 10), camera_id="cam-1",
        people_count=2, vehicle_count=3, crowd_density=4.5,
        fps=12.0, traffic_per_minute=7,
    )
    db = MagicMock()
    db.scalars.side_effect = [[], [sample]]
    monkeypatch.setattr(main, "SessionLocal", lambda: db)
    monkeypatch.setattr(main.hub, "latest", {})
    result = main.analytics()
    assert result["density_trend"] == [{
        "timestamp": "2026-11-24T09:10:00+00:00", "camera_id": "cam-1",
        "people_count": 2, "vehicle_count": 3,
        "crowd_density_per_megapixel": 4.5, "fps": 12.0,
        "vehicles_per_minute": 7,
    }]
