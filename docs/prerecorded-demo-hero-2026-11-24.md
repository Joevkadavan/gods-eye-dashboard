# GOD’S EYE cinematic prerecorded demo hero — 2026-11-24

## Delivered

- Promoted the existing `indian-urban-traffic-demo` to the Overview landing hero, directly below the website header. It plays the bundled Pexels MP4 through a dedicated same-origin API route; the source is not replaced by static frames.
- The video route is restricted to that bundled demo and supports HTTP byte ranges through Starlette `FileResponse`, including through the Next.js `/api/*` rewrite. Inline disposition lets the browser seek/autoplay the MP4.
- Added a lightweight telemetry route exposing the exact latest inference detections/metrics plus the worker’s media position. The hero overlays only actual detector boxes when media position is sufficiently aligned; it seeks back to the worker frame when drift exceeds the threshold and labels when YOLO is not synced.
- Added muted autoplay/loop, inline mobile playback, play/pause, restart, mute/unmute, volume slider, fullscreen, loading/error states, source and playback state, people/vehicle counts, inference FPS, analytics sync state, Pexels credit, and a link to the existing YOLO station.
- Kept the title honest: India / city not verified; explicitly marked prerecorded and not live CCTV. No demo map coordinates were added.
- Reordered the overview below the hero: Situational Overview KPIs → Verified India Camera Views → Interactive India map → Alerts Requiring Review → Activity Snapshot → Recent Events. Existing pages and the camera/video inventory remain in place.
- Added responsive desktop/tablet/mobile hero rules, touch-sized buttons, reduced-motion handling, and narrow-screen-specific control wrapping.

## Verification

- `npm run build` — passed on the final source state.
- `python3 -m pytest -q backend/tests` — **18 passed**.
- Runtime API: API starts, telemetry returned real detections/metrics (`1920×1080`, observed `13.3` inference FPS in the checked sample), and `GET` with `Range: bytes=0-1023` through the running Next.js rewrite returned **206 Partial Content**, 1024 bytes, `video/mp4`, inline disposition, and `Accept-Ranges: bytes`.
- Homepage returned HTTP 200 and server-rendered copy for the hero and ordered dashboard sections.
- No Chromium/Firefox binary or Playwright/Puppeteer installation is present in the workspace. Therefore desktop/mobile visual browser inspection and measured overflow checks have **not** been completed; use the live dashboard preview for that final visual QA.
