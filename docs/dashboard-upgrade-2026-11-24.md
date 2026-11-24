# Dashboard upgrade implementation — 2026-11-24

## Audit

The full prioritized audit is in `docs/frontend_audit_2026-11-24.md`. Key verified issues before this implementation: the schematic SVG map lacked a projection and admin boundaries; camera denominators mixed unlike feed groups; pending safety alerts included informational/demo lifecycle events; analytics event bars showed event ordinal rather than a count; the incidents verification-state select did not filter; API polling was every 2.5 seconds; cards overlaid camera labels/actions on images; and metric tables substituted zero when data was missing.

## Implemented

- Replaced the schematic SVG map with MapLibre GL JS and a real interactive vector basemap. Added a compact 36-feature Natural Earth India Admin-1 reference GeoJSON, camera-registry-only marker points, selectable markers plus accessible source-list controls, health filter, zoom/reset, boundary visibility, pitch and source-style building-extrusion switch, visible basemap attribution, and an unavailable/loading state.
- Explicit map/source limitations: Natural Earth generalized Admin-1 reference boundaries are not authoritative/legal. Natural Earth city points were not used as camera locations. OpenFreeMap is a third-party tile service with no SLA implied. Demo clips have no map coordinates.
- Added status-specific available/unavailable marker colors, accurate point count, coordinates/source labels, and 3D option from existing mapped buildings only—no invented terrain height or satellite imagery.
- Improved reusable interaction feedback for navigation/KPI icons using a lightweight Lucide wrapper/CSS. No icon animation dependency added. Existing reduced-motion settings remain in force.
- Reworked camera cards: source name/location, state and actions are no longer layered over the source image; dedicated open-station action remains. Still-image sources disclose periodicity and no AI processing; provider embed reload is not described as a capture refresh. Prerecorded video is labelled DEMO, not LIVE, with city-unverified context.
- Corrected status denominator labels to separate India-registered sources from the configured prerecorded demo. Live people/vehicle KPI footnotes identify when demos contribute. Missing system/current camera measurements render as `—`, not invented zeroes.
- Changed dashboard data polling to 10 seconds while preserving a 1-second local clock; still retains fast polling only in the open synchronized frame station.
- Analytics supports 1/6/24-hour display windows over actual returned persisted records. Backend event frequency now counts persisted events per populated UTC hour (no fabricated event ordinals or empty buckets). Camera metric history remains the stored samples; no CPU history is claimed or synthesized.
- Fixed the incident verification-state control and kept severity/state filtering functional. Actionable alert counts exclude informational lifecycle and demo event categories; starting a prerecorded file no longer creates a pending “alert.” Historical informational rows remain in the event ledger and are not deleted.
- Added HTTP error feedback to event and camera actions.
- Updated Next.js to 15.5.29, MapLibre GL JS to 6.4.1, PostCSS to 8.5.33 with an override that patches Next's nested version, and added `package-lock.json`. `npm audit` reports zero vulnerabilities.

## Changed files

- `frontend/app/IndiaMap.tsx` — MapLibre interactive map component.
- `frontend/app/page.tsx` — dashboard integration, data labels, real-history filtering, event filters and camera cards.
- `frontend/app/globals.css` — responsive map/card/icon and reduced-motion styling.
- `frontend/package.json`, `frontend/package-lock.json` — MapLibre/security updates.
- `frontend/public/data/india_admin1.geojson` — compact generalized India Admin-1 reference map data.
- `backend/main.py` — alert classification/count and persisted hourly event count grouping; demo lifecycle event behavior.
- `backend/tests/test_dashboard_data.py`, `backend/tests/test_map_asset.py` — unit/asset checks.
- `scripts/build_india_admin1.py` — reproducible external-data asset generator.
- `docs/frontend_audit_2026-11-24.md`, `docs/geospatial-map.md`, `docs/dashboard-upgrade-2026-11-24.md`, `docs/architecture.md`, `README.md`, `PROJECT_STATUS.md` — audit, provenance/limitations and operations notes.

## Backend/API impact

No routes, existing response envelopes/fields, database tables, camera data model, authentication model, YOLO flow, or source registration were removed or renamed. `/api/overview` keeps its existing keys, with `active_alerts` now representing actionable pending items only. `/api/analytics.event_frequency` preserves its existing individual-event row shape; a new additive `event_frequency_buckets` field supplies `{timestamp, count}` UTC hour buckets for the chart (the old frontend incorrectly treated event order as a count). Event persistence remains unchanged; only prerecorded start lifecycle rows stop being emitted. Existing informational rows remain stored.

## Verification

- `cd frontend && npm run build` — passed on Next.js 15.5.29 and MapLibre GL JS 6.4.1 (optimized build and TypeScript checks).
- `cd frontend && npm audit` — zero vulnerabilities after updates/override.
- `cd backend && pytest -q tests` — **17 passed**, including actionable alert classification, hourly bucket generation, API compatibility/additive analytics field, and offline GeoJSON asset validation tests.
- Runtime smoke: `/api/health`, `/api/overview`, `/api/analytics`, same-origin `/api/overview`, dashboard `/`, and `/data/india_admin1.geojson` all returned HTTP 200. Confirmed backend output has zero actionable pending alerts (older informational DEMO rows remain in history), two India still-image sources, and additive analytics `event_frequency_buckets` returns actual hourly `{timestamp,count}` buckets while preserving the original event-row field.
- No browser automation runtime (Chromium/Firefox/Playwright/Puppeteer) is available in the workspace, so visual browser interaction, map tiles, and narrow-screen rendering must be manually checked in a real browser. Build success does not claim that map provider access is available in every deployment.

## Limitations / follow-up

- Map tile style relies on the public OpenFreeMap endpoint and external network access. Configure/self-host an appropriate service for reliability requirements; preserve attribution.
- Natural Earth is generalized/stale-prone cartographic reference data. Do not use the overlay for jurisdiction, legal boundaries, navigation or response decisions.
- Only camera registry records with verified coordinate fields appear; existing Chennai feeds are still-image embeds and the India demo is unlocated.
- System CPU/memory is a live snapshot only; no persisted CPU history table/chart was added. Analytics filters cannot extend beyond the API's actual returned retention/count cap.
- No generative AI assistant was introduced; there is no new inference provider. Existing YOLO detections remain the only image/video AI outputs and keep their current limitations.
- Existing card and dashboard shell architecture is retained; no route or backend deployment config was replaced. No camera data was modified to add coordinates.
