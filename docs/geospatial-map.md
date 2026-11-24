# GOD'S EYE map data, attribution, cost and display limitations

## Map features

- MapLibre GL JS renders an OpenStreetMap-derived OpenMapTiles vector basemap served by OpenFreeMap. The dark intelligence style is the default; Dark, Liberty, Positron and Bright are selectable. Streets, primary roads, waterways and place labels come from the vector style.
- Pan, wheel/touch zoom, keyboard/compass navigation, drag rotation, tilt, fullscreen, India reset and city fly-to are supported. MapLibre is dynamically imported only when the map approaches the viewport. Style changes reuse the map instance; app layers are reattached after style reloads.
- The optional 3D toggle pitches the view and enables a MapLibre fill-extrusion layer over OpenMapTiles `building` vector features at high zoom. Extrusion height uses mapped `render_height`/`height` attributes when present; unmapped buildings do not appear. No separate buildings API is called.
- A satellite/imagery option is omitted by default. It appears only when `NEXT_PUBLIC_SATELLITE_STYLE_URL` is configured at build time. An operator must provide a properly licensed MapLibre style URL with the required imagery terms and attribution. Any provider token embedded in this browser-facing `NEXT_PUBLIC_` URL is public; restrict it as the provider supports. Do not place server secrets in a public style URL. No imagery provider or paid plan is selected by this project.

## Registry and boundaries

- Camera points come only from the existing camera registry with finite coordinates inside India. Markers are a compact GeoJSON source + MapLibre circle layers (not one DOM node per camera). The two Chennai camera pins use their stored coordinates; filtering and source selection do not fabricate locations.
- `frontend/public/data/india_admin1.geojson` is a locally bundled, simplified 36-feature ADM1 GeoJSON based on the pinned geoBoundaries `gbOpen` India ADM1 source. Attribution: geoBoundaries / William & Mary geoLab, CC BY 4.0. The boundary is a cartographic reference, not a legal/cadastral determination or a guarantee of every disputed boundary. Original release: https://github.com/wmgeolab/geoBoundaries/tree/9469f09/releaseData/gbOpen/IND/ADM1 . API/source docs: https://www.geoboundaries.org/api.html
- Geometry is simplified for client rendering. State/UT polygons are served locally; the user’s browser does not fetch boundary API data at runtime. The generator is `scripts/build_india_admin1.py`.
- Camera popover values (name, city/state, coordinates, health status, `last_image_at`) come from stored camera data. Missing last-image timestamps display “Not recorded”; no timestamps or availability are synthesized. “Open Camera” invokes the existing camera station viewer.

## Free map provider, terms and costs

- Default provider: OpenFreeMap public vector styles, currently `https://tiles.openfreemap.org/styles/dark`, built on OpenMapTiles/OpenStreetMap data. As checked 2026-11-24, OpenFreeMap says its public instance is free, commercial use is allowed, no API key/registration is required, and there is no stated map-view/request quota. These are provider terms, not an uptime guarantee.
- OpenFreeMap terms are “as-is,” with no SLA or availability guarantee and say the provider may discontinue the service. A provider outage or future terms/service change can affect the basemap. The code introduces no paid map API, subscription, or Google Maps dependency. There is no map-view invoice from OpenFreeMap under its published public-instance terms, but a move to another provider or self-hosting can have costs.
- OpenFreeMap offline downloads: each user-started download is limited to 3,000 tiles / 50 MB, at most four parallel requests, with a unique identifying User-Agent; this app does not implement offline bulk downloads.
- Visible MapLibre attribution is retained. OpenFreeMap’s stated attribution is “OpenFreeMap · © OpenMapTiles · Data from OpenStreetMap”; OSM data is ODbL and requires credit. The app separately credits the local geoBoundaries boundary dataset (CC BY 4.0).
- Source terms: https://openfreemap.org/ · https://openfreemap.org/tos/ · https://openfreemap.org/quick_start/ · https://www.openstreetmap.org/copyright

## Verification and deployment notes

- The checked-in GeoJSON is validated by `backend/tests/test_map_asset.py`.
- Frontend deployment uses `frontend/next.config.mjs`; for Vercel, the GOD'S EYE frontend project must have `API_URL` pointed at a reachable, deployed FastAPI backend. The local default `127.0.0.1:8000` is not a valid Vercel backend URL.
- Do not deploy this application to another unrelated Vercel project. The connected Vercel account currently exposes a production project named `bealwaysjoe`, whose live production site is a creator-services website, not GOD'S EYE. A matching GOD'S EYE project/deployment is not present in the connected Vercel project list. Production testing is therefore pending the correct GOD'S EYE Vercel project/repository and backend URL.
