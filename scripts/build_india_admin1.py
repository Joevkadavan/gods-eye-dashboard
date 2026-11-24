#!/usr/bin/env python3
"""Build a compact, attribution-compliant GeoJSON reference of India ADM1.

Run from the repository root after `python -m pip install shapely`. Uses a
pinned geoBoundaries gbOpen release; no service/API is needed at app runtime.
"""
from __future__ import annotations
import json
from pathlib import Path
from urllib.request import Request, urlopen
from shapely.geometry import mapping, shape

SOURCE = "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/IND/ADM1/geoBoundaries-IND-ADM1_simplified.geojson"
OUTPUT = Path("frontend/public/data/india_admin1.geojson")
request = Request(SOURCE, headers={"User-Agent": "GODS-EYE-map-asset-builder/1.0"})
with urlopen(request, timeout=90) as response:
    source = json.load(response)
features = []
for feature in source["features"]:
    props = feature["properties"]
    geometry = shape(feature["geometry"]).simplify(0.005, preserve_topology=True)
    if geometry.is_empty:
        continue
    features.append({
        "type": "Feature",
        "properties": {
            "name": props.get("shapeName"),
            "iso": props.get("shapeISO"),
            "source": "geoBoundaries gbOpen India ADM1",
        },
        "geometry": mapping(geometry),
    })
if len(features) != 36:
    raise SystemExit(f"Expected 36 India ADM1 state/UT records, got {len(features)}; asset was not written")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps({
    "type": "FeatureCollection",
    "name": "India state and union territory reference boundaries",
    "features": features,
}, separators=(",", ":")))
print(f"Wrote {len(features)} geoBoundaries ADM1 references to {OUTPUT}")
