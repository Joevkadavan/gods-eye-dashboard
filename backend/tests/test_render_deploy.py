import pytest

import main
from db import resolve_database_url


def test_production_database_url_must_be_persistent_postgres():
    with pytest.raises(RuntimeError, match="persistent PostgreSQL"):
        resolve_database_url("sqlite:///../data/godseye.db", app_env="production", is_render=True)
    with pytest.raises(RuntimeError, match="persistent PostgreSQL"):
        resolve_database_url(None, app_env="production", is_render=True)


def test_local_sqlite_remains_available_for_development():
    assert resolve_database_url(None, app_env="development", is_render=False) == "sqlite:///../data/godseye.db"


def test_supabase_postgres_url_uses_psycopg_and_requires_tls_in_production():
    actual = resolve_database_url(
        "postgresql://postgres.example:fake-password@pooler.example:5432/postgres",
        app_env="production",
        is_render=True,
    )
    assert actual.startswith("postgresql+psycopg://")
    assert actual.endswith("?sslmode=require")


def test_supabase_url_preserves_query_and_adds_ssl_requirement():
    actual = resolve_database_url(
        "postgres://user:fake-password@pooler.example:5432/postgres?application_name=godseye",
        app_env="production",
        is_render=True,
    )
    assert actual.startswith("postgresql+psycopg://")
    assert "application_name=godseye&sslmode=require" in actual


def test_production_cors_origin_parser_accepts_exact_origins_only():
    assert main.parse_frontend_origins("https://site.example, https://preview.example/") == [
        "https://site.example",
        "https://preview.example",
    ]


def test_overview_does_not_report_zero_counts_without_any_inference(monkeypatch):
    from unittest.mock import MagicMock

    db = MagicMock()
    db.scalars.side_effect = [[], [], []]
    monkeypatch.setattr(main, "SessionLocal", lambda: db)
    monkeypatch.setattr(main.hub, "latest", {})
    actual = main.overview()
    assert actual["people_detected"] is None
    assert actual["vehicles_detected"] is None
    assert actual["fps"] is None


def test_free_profile_can_skip_ephemeral_evidence_writes(monkeypatch):
    monkeypatch.setattr(main, "LOCAL_EVIDENCE_ENABLED", False)
    assert main.save_evidence("event-id", object()) is None


def test_render_health_checks_database_without_leaking_connection_string(monkeypatch):
    class Connection:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def execute(self, statement):
            assert str(statement) == "SELECT 1"

    class Engine:
        dialect = type("Dialect", (), {"name": "postgresql"})()
        def connect(self):
            return Connection()

    monkeypatch.setattr(main, "engine", Engine())
    actual = main.render_health()
    assert actual == {"status": "ok", "database": "postgresql", "video_analytics": "enabled" if main.VIDEO_ANALYTICS_ENABLED else "disabled"}
