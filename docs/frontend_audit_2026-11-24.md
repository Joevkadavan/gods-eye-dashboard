# GOD'S EYE dashboard audit — 2026-11-24

## Scope and evidence checked

Audited the existing Next.js 15 / React 19 / TypeScript single-page command dashboard (`frontend/app/page.tsx`, `globals.css`, `layout.tsx`, `package.json`, and `next.config.mjs`), the FastAPI/SQLAlchemy/SQLite-or-PostgreSQL backend (`backend/main.py`, `db.py`, `cv_engine.py`, requirements), current camera/event rows in the working SQLite database, the existing tests and camera/video documentation. The dashboard currently has no Framer Motion, GSAP, Three.js, map library, or geospatial asset dependency; existing motion is CSS-based. The map is a hand-drawn SVG with a linear lon/lat-to-pixel transform—not a projected map. The inline video viewer already uses the synchronized YOLO frame API and backend playback actions added in the previous upgrade.

## Prioritised findings

### Critical — data integrity and source interpretation

1. **Source denominator inconsistency is a presentation bug, not a data-source discrepancy.** The top status pill counts the two verified Chennai image-refresh records; the page header counts all three configured records, which also includes the Indian prerecorded demo. Current database evidence: two `image_refresh` sources online plus one `demo` source online. These ratios answer different questions but both were labelled “endpoints available,” making 2/2 and 3/3 appear contradictory. Fix by naming the source groups and their denominators explicitly; never merge the demo into public/live camera counts.
2. **People/vehicle KPI provenance is real but insufficiently obvious.** `/api/overview` sums `hub.latest` over every processed video source, including the packaged demo; it does not read the Chennai still images. The values are genuine detector outputs, but their label does not identify which video sources contribute. Expose live/demo feed counts and make KPI freshness/source notes explicit rather than excluding real measurements or substituting placeholders.
3. **Repeated demonstration startup records are present.** The database contains four pending `DEMO_PLAYBACK_STARTED / INFORMATIONAL` rows for the single demo camera. The worker emits a lifecycle event at each launch and `active_alerts` counts every pending record regardless of severity. Stop creating alert records for demo startup, exclude informational lifecycle events from pending safety alerts, and group retained historical duplicates without deleting or rewriting their event history.
4. **Map precision and boundary provenance are overstated by the SVG.** Two geolocated sources are only the two Chennai still-image embeds. The demo has no coordinates. The hand-authored outline cannot support state filtering, real distances, rotation, hit-testing, or accurate relative geography. Replace it with a projected interactive map and sourced state/city data; map only registered camera coordinates and state that the basemap/boundaries are cartographic reference data, not an authoritative survey or legal border product.

### Major — interaction and visual hierarchy

- Camera names, location chips, and actions are positioned over the image with absolute overlays. Long labels and narrow cards can cover image content or crowd one another. Put source metadata/actions in a separate card header/footer with a bounded image viewport.
- There is no camera image reload action, and source availability can be mistaken for image freshness. Distinguish an embed reload from the provider's actual refresh schedule and show `last_checked_at` / `last_image_at` separately.
- Alert list has only all/critical/warning/informational filters; verification-state select is uncontrolled and does not filter. Events are not grouped, evidence is a text link rather than a preview, and lifecycle/demo records share the same list treatment as operator-review cues. Keep backend acknowledgement/verification/dismissal actions and make these distinctions visible.
- `EVENT FREQUENCY` currently maps ordered events to an increasing `n = i + 1`; that is event ordinal, not a frequency count. Group actual events into real time buckets. Do not fill missing history with synthetic values.
- Analytics is not range-filtered, and `/api/analytics` caps history at 3,000 metrics and 1,000 events. Camera metric samples exist every ~10 seconds; CPU/system samples and historical source-check/refresh rows do not exist. Add sparse actual history records with retention and range-aware queries, and show an empty/not-retained state where records are absent.
- Main dashboard polling calls overview, events, analytics, and settings every 2.5 seconds. Settings do not need this cadence. Keep the live clock separate; use slower polling for persistent dashboard data and retain faster uncached polling only inside an open processed-frame viewer.
- The existing page and CSS are large and compressed into monolithic render blocks; this makes feature integration and responsive maintenance riskier. Extract the map, icon system, operations assistant, alert group and data-viz components while preserving the current page-state navigation and endpoints.

### Minor — polish and accessibility

- Lucide icons are reused but are mostly static; buttons have limited busy/error feedback and icon motion is inconsistent. Introduce one small reusable icon wrapper with interaction/state-specific CSS rather than installing several animation/3D packages or animating every icon.
- The existing dark palette is a sound starting point; hierarchy, spacing, focus states, source-state semantics, camera labels, chart titles/units and consistent loading/empty states need refinement. Continue to respect reduced motion and avoid animation tied to object-detection coordinates.
- The sidebar names `Live Monitoring` and the camera tab, but alerts/evidence and source registry are not consistently reflected in page hierarchy. Preserve existing working page-state navigation and routes; improve naming/context rather than silently deleting pages.

### Recommended capabilities

- MapLibre GL JS with OpenFreeMap/OpenStreetMap tiles, locally bundled Natural Earth Admin-1 polygons and major-populated-place points. MapLibre is the renderer, not the data provider; use the provider's required attribution. Use camera coordinates only when present. The basemap's Liberty style includes a 3D building layer; a 2D/tilted 3D toggle can expose mapped building extrusions without inventing terrain heights. Satellite imagery should only activate when a licensed tile provider is configured.
- A small deterministic operations assistant backed by the currently loaded API data can answer source-health, city-count and pending-alert questions and explicitly say when historical CPU samples are not retained. This is not an LLM and must not claim video analysis. Keep its provider interface modular for a later authorized language-model integration.
- Actual source-health and system CPU/memory samples can support availability, refresh, and performance charts after first startup; show empty states until samples accumulate. Restrict configured timespans to retained history and label the current demo distinctly.

## Engineering choice

The project has no current animation/map framework. Reuse Lucide and lightweight CSS/React transitions; add MapLibre GL JS for the genuinely interactive map only. OpenFreeMap uses OSM data and requires attribution; the Natural Earth admin-1 source is generalized cartographic data with a documented de-facto-boundary policy and currency caveat. Do not add Three.js, Lottie, Rive, Cesium, deck.gl, or a fabricated terrain surface when MapLibre plus actual OSM building footprints and explicit reference boundaries meets the need.
