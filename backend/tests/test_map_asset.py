import json
from pathlib import Path


def test_bundled_india_admin1_asset_is_reference_boundaries_not_camera_locations():
    asset = Path(__file__).resolve().parents[2] / "frontend/public/data/india_admin1.geojson"
    data = json.loads(asset.read_text())
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 36
    iso_codes = {f["properties"]["iso"] for f in data["features"]}
    assert {"IN-TN", "IN-LA", "IN-PY"} <= iso_codes
    assert all(f["properties"]["source"] == "geoBoundaries gbOpen India ADM1" for f in data["features"])
    assert all(code for code in iso_codes)
    assert "state and union territory" in data["name"]
    assert all(f["geometry"]["type"] in {"Polygon", "MultiPolygon"} for f in data["features"])
    assert "latitude" not in data["features"][0]["properties"]
