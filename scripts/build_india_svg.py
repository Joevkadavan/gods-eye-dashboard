#!/usr/bin/env python3
"""Generate the compact local SVG India ADM1 map from the pinned gbOpen GeoJSON."""
import json
from pathlib import Path
SOURCE = Path('frontend/public/data/india_admin1.geojson')
OUTPUT = Path('frontend/public/data/india_states.svg')
WIDTH, HEIGHT, SCALE_X, SCALE_Y, LON_MIN, LAT_MAX = 900, 990, 28.0, 30.0, 67.0, 37.5

def project(point):
    lon, lat = point[:2]
    return round((lon-LON_MIN)*SCALE_X,1), round((LAT_MAX-lat)*SCALE_Y,1)
def ring_path(ring):
    pts=[project(p) for p in ring]
    if len(pts)<4:return ''
    return 'M'+' '.join((f'{x},{y}' if i==0 else f'L{x},{y}') for i,(x,y) in enumerate(pts))+'Z'
def polygon_path(poly):return ''.join(ring_path(r) for r in poly)
def geometry_path(g):
    if g['type']=='Polygon':return polygon_path(g['coordinates'])
    if g['type']=='MultiPolygon':return ''.join(polygon_path(p) for p in g['coordinates'])
    return ''
fc=json.loads(SOURCE.read_text())
parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc"><title id="title">India state and union territory boundaries</title><desc id="desc">Simplified geoBoundaries gbOpen India ADM1 reference map. CC BY 4.0; not a legal boundary.</desc><g fill="#102632" stroke="#52c9d0" stroke-width="1.45" stroke-linejoin="round" stroke-linecap="round">']
for f in fc['features']:
    p=f['properties'];name=p.get('name') or 'State or union territory';iso=p.get('iso') or ''
    parts.append(f'<path id="state-{iso}" data-name="{name}" data-iso="{iso}" d="{geometry_path(f["geometry"])}"/>')
parts.append('</g></svg>')
OUTPUT.write_text(''.join(parts))
print(f'Wrote {len(fc["features"])} features ({OUTPUT.stat().st_size:,} bytes) to {OUTPUT}')
