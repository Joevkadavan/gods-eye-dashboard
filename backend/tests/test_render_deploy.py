import os
from pathlib import Path
import subprocess
import sys

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
        "postgresql://postgres.example:fake-password@aws-0-test.pooler.supabase.com:5432/postgres",
        app_env="production",
        is_render=True,
    )
    assert actual.startswith("postgresql+psycopg://")
    assert actual.endswith("?sslmode=require")


def test_supabase_url_preserves_query_and_adds_ssl_requirement():
    actual = resolve_database_url(
        "postgres://user:fake-password@aws-0-test.pooler.supabase.com:5432/postgres?application_name=godseye",
        app_env="production",
        is_render=True,
    )
    assert actual.startswith("postgresql+psycopg://")
    assert "application_name=godseye&sslmode=require" in actual


def test_production_session_pooler_must_use_supabase_session_hostname_and_port():
    with pytest.raises(RuntimeError, match="Session Pooler"):
        resolve_database_url("postgresql://user:pw@db.project.supabase.co:5432/postgres", app_env="production", is_render=True)
    with pytest.raises(RuntimeError, match="port 5432"):
        resolve_database_url("postgresql://user:pw@aws-0-test.pooler.supabase.com:6543/postgres", app_env="production", is_render=True)


def test_production_cors_origin_parser_accepts_exact_origins_only():
    assert main.parse_frontend_origins("https://site.example, https://preview.example/") == [
        "https://site.example",
        "https://preview.example",
    ]
    assert main.is_exact_https_origin("https://gods-eye-dashboard-tau.vercel.app")
    assert not main.is_exact_https_origin("https://gods-eye-dashboard-tau.vercel.app/operations")
    assert not main.is_exact_https_origin("http://gods-eye-dashboard-tau.vercel.app")


def test_admin_bearer_token_required_in_production(monkeypatch):
    from fastapi import HTTPException

    token = "t" * 48
    monkeypatch.setattr(main, "IS_PRODUCTION", True)
    monkeypatch.setattr(main, "ADMIN_API_TOKEN", token)
    assert main.require_admin(f"Bearer {token}") is True
    assert main.require_admin(f"bearer {token}") is True
    with pytest.raises(HTTPException) as denied:
        main.require_admin("Bearer wrong")
    assert denied.value.status_code == 401
    with pytest.raises(HTTPException):
        main.require_admin(None)


def test_all_http_write_routes_have_admin_dependency():
    protected = {
        (route.path, method)
        for route in main.app.routes
        if hasattr(route, "dependant") and any(dep.call is main.require_admin for dep in route.dependant.dependencies)
        for method in (route.methods or set())
    }
    expected = {
        ("/api/cameras", "POST"),
        ("/api/cameras/upload", "POST"),
        ("/api/cameras/{camera_id}", "PATCH"),
        ("/api/cameras/{camera_id}", "DELETE"),
        ("/api/events/{event_id}/verify", "PATCH"),
        ("/api/cameras/{camera_id}/playback", "POST"),
        ("/api/settings", "PUT"),
    }
    all_writes = {
        (route.path, method)
        for route in main.app.routes
        if hasattr(route, "methods")
        for method in (route.methods or set())
        if method in {"POST", "PUT", "PATCH", "DELETE"}
    }
    assert all_writes == expected
    assert expected <= protected


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


def test_api_only_mode_imports_without_vision_libraries():
    backend = Path(__file__).resolve().parents[1]
    script = r'''import importlib.abc, sys
class BlockVision(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'cv2', 'numpy', 'onnxruntime', 'sklearn'}:
            raise ModuleNotFoundError('vision packages intentionally excluded')
sys.meta_path.insert(0, BlockVision())
import main
assert main.VIDEO_ANALYTICS_ENABLED is False
assert main.cv2 is None
assert main.detector is None
'''
    env = {**os.environ, "PYTHONPATH": str(backend), "ENABLE_VIDEO_ANALYTICS": "false", "DATABASE_URL": "sqlite:///:memory:"}
    subprocess.run([sys.executable, "-c", script], cwd=backend, env=env, check=True, capture_output=True, text=True)


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
