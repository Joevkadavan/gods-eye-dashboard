from datetime import timezone
from unittest.mock import MagicMock, patch
import pytest
from main import INDIA_FEEDS, check_still_source


def test_india_registry_has_verified_chennai_coordinates_and_attribution():
    assert len(INDIA_FEEDS) == 2
    for feed in INDIA_FEEDS:
        assert feed["city"] == "Chennai"
        assert 6 <= feed["latitude"] <= 38
        assert 68 <= feed["longitude"] <= 98
        assert feed["still_url"].startswith("https://opencctv.org/still/")
        assert feed["embed_url"].startswith("https://opencctv.org/embed/")
        assert feed["page_url"].startswith("https://opencctv.org/cameras/india/")


def test_still_health_check_validates_jpeg_and_parses_source_modified_time():
    response = MagicMock()
    response.status = 200
    response.headers = {"Content-Type": "image/jpeg", "Last-Modified": "Tue, 24 Nov 2026 16:43:58 GMT"}
    response.read.return_value = b"\xff\xd8\xff\xe0" + b"x" * 28
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    with patch("main.urllib.request.urlopen", return_value=response):
        modified = check_still_source("https://example.test/image.jpg")
    assert modified is not None
    assert modified.tzinfo is not None
    assert modified.astimezone(timezone.utc).year == 2026


def test_still_health_check_rejects_html_or_non_jpeg_payload():
    response = MagicMock()
    response.status = 200
    response.headers = {"Content-Type": "text/html"}
    response.read.return_value = b"<html>not a feed</html>".ljust(32, b" ")
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    with patch("main.urllib.request.urlopen", return_value=response):
        with pytest.raises(ValueError, match="Expected JPEG"):
            check_still_source("https://example.test/not-an-image")
