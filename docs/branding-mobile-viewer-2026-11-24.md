# Branding, responsive navigation and camera viewer — 2026-11-24

## Delivered

### Brand / eye mark

- Moved **MADE BY JOE V KADAVAN** directly into the sidebar brand lockup, under the product descriptor; a compact version appears beside the mobile header logo.
- Replaced the plain Lucide eye in the main brand and camera-viewer brand with a small inline SVG/CSS eye mark: dark metallic housing, reflective cyan iris, glint, subtle 3D hover, gentle eye movement, and irregular timer-driven blinks at roughly 3.4–7.2-second intervals. CSS/SVG only—no Three.js or additional package. Reduced-motion users get no blink, iris motion, or hover transform. This is a lightweight stylized 3D treatment, not a physically rendered 3D model.

### Responsive navigation and layout

- Desktop retains its fixed left command-center sidebar.
- Tablet widths from 721–1100 px use a menu button with a slide-in drawer and scrim.
- At widths ≤720 px the sidebar becomes a six-icon bottom navigation bar, with accessible button names. The compact product mark and creator credit move to the top bar. KPIs remain a two-column grid; camera cards and major content stack. Safe-area padding, horizontally contained tables, touch targets, map controls, and mobile camera-sheet styling are provided.
- The full-screen camera view uses small-screen and landscape rules; the source-information panel becomes a collapsible bottom sheet on mobile.

### Camera images / immersive viewer

Inspected `CameraTile`, the FastAPI camera registry/serializer and the actual `/api/overview` records. Existing cross-origin OpenCCTV `source_url` embeds remain the image provider integration; the viewer does not replace them with fabricated preview URLs or downloaded imagery. A click/touch target now overlays each camera image, with the existing **OPEN STATION** action retained. The fullscreen dialog also offers an external provider source-page action when the embed is unavailable/restricted.

The live registry returned:

| Station | City / State | Coordinates | Provider embed | Registry refresh interval |
|---|---|---:|---|---:|
| Choolaimedu High Road | Chennai, Tamil Nadu | 13.06372, 80.23031 | `https://opencctv.org/embed/302297` | 600 seconds |
| Tiruvottiyur | Chennai, Tamil Nadu | 13.19230, 80.31570 | `https://opencctv.org/embed/313940` | 150 seconds |

The station viewer reads these values independently from its selected camera object; coordinates, names, provider links, source classification, check status, health message, refresh interval, last source check and last image-modification timestamp come from existing camera records. Unknown values show “not recorded/supplied” rather than defaults. Timestamps are formatted from the actual API timestamps.

The still-image viewer explicitly says **STILL IMAGE SOURCE – NOT CONTINUOUS VIDEO**, that provider refresh/capture is external, and that there are no still-image YOLO detections or video controls. The information button toggles between **HIDE INFORMATION** and **SHOW INFORMATION**; the existing camera pane layout expands the image area when closed. On desktop it uses a side panel; mobile uses an expandable overlay sheet. Browser fullscreen is an explicit action; the whole application modal fills the viewport independently. Escape, Close, outside-layout clicks, existing camera switching and body-scroll restoration are wired.

## Preservation

- No APIs, routes, camera records, source URLs, backend source schedules, database schema or YOLO/frame workflow changed for this work.
- Both station actions select the camera ID; the source panel reads metadata for that selected camera. Existing video/demo fullscreen processing, playback controls, keyboard shortcuts and human-review caveats remain.

## Checks and limits

- `cd frontend && npm run build` — passed after the UI changes.
- `cd backend && pytest -q tests` — **17 passed** (existing plus previous audit/analytics/map tests; no backend change in this branding/viewer update).
- Runtime smoke: dashboard page, same-origin overview and bundled map data returned HTTP 200. The overview values for both image sources matched the table above.
- The environment has no Chromium, Chrome, Firefox, Playwright or other browser automation executable. Thus, the requested 360/390/430 px and tablet visual screenshots, mobile portrait/landscape interaction, iframe visual aspect, and browser-console checks could not be truthfully marked as automated/passed. CSS includes explicit 390 px, 520 px, 720 px, 850 px, 1100 px and landscape breakpoints, but a real-device/browser visual pass remains necessary.
- OpenCCTV remains a cross-origin provider-controlled embed. Browser fullscreen applies to the GOD’S EYE viewer; an external provider may restrict its own embedded controls. The source page link is retained as the fallback; the app does not claim to control the provider's capture cadence.
