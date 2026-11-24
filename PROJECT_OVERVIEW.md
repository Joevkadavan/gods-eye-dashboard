# GOD'S EYE – PROJECT OVERVIEW

## A. Why I Started GOD'S EYE

I started GOD'S EYE with a vision of exploring how artificial intelligence, computer vision, geographic intelligence and video analytics could come together in an accessible public safety intelligence platform. I wanted to bring visual monitoring, people and vehicle detection, camera-source information, geographic visualisation and concise event summaries into one dashboard—while keeping human review central.

## B. What Is GOD'S EYE?

GOD'S EYE is an AI-assisted public safety intelligence and situational-awareness dashboard prototype. It combines a processed prerecorded traffic demonstration, a registry of verified camera sources, computer-vision metrics, map context and reviewable events. It is a software prototype—not a certified emergency-response or live city-surveillance system.

## C. Key Features

- **Indian traffic video hero:** a seekable, looping Pexels traffic video clearly labelled prerecorded and not live CCTV. The city is not verified.
- **AI video intelligence:** CPU-based YOLOv8n/ONNX inference for people and selected vehicle classes, with confidence, bounding boxes, camera-local temporary tracking IDs, counts and inference timing.
- **Animated eye branding:** a lightweight SVG/CSS eye mark, with subtle motion and reduced-motion support.
- **Camera registry and viewer:** source metadata, availability checks, provider links, periodic image refreshes and an existing fullscreen station viewer. The Chennai registry entries are periodic still-image sources; they are not continuous video or YOLO-processed.
- **Interactive India map:** MapLibre GL JS, OpenStreetMap-derived vector tiles, state/UT reference boundaries, city navigation, map controls, selectable camera markers and optional mapped-building extrusions.
- **Alerts requiring review and Recent Events:** stored events are presented for human acknowledgement, verification or dismissal.
- **Activity analytics, responsive navigation and system monitoring:** retained metric charts, CPU/runtime telemetry and layouts for desktop and mobile.

Counts and event cues are model outputs and prototype heuristics, not ground-truth measurements. Alerts are not judgments of identity, intent or dangerousness.

## D. Technology and Innovation

The frontend is Next.js 15 with React 19, TypeScript, MapLibre GL JS and Recharts. A Python FastAPI backend exposes the REST and WebSocket APIs and runs OpenCV video workers. YOLOv8n exported to ONNX Runtime performs CPU inference; a small IoU tracker creates temporary, camera-local IDs. SQLAlchemy uses SQLite by default and can be configured for PostgreSQL. OpenFreeMap serves OpenStreetMap/OpenMapTiles-derived vector styles without a Google Maps API. Vercel is the intended host for the Next.js frontend; a separately hosted, reachable FastAPI backend is required for registry and analytics data.

## E. Public Accessibility

The site is intended to be viewable in a normal browser without installing the development environment. **A GOD'S EYE production URL is not available yet.** The preferred `https://gods-eye-dashboard.vercel.app` currently serves an unrelated “God's Eye | Cyber Chief” application, so it must not be advertised or overwritten. The connected Vercel account has no matching GOD'S EYE project. A production URL can be added here after the correct project, repository and backend endpoint are connected and deployment is verified.

When deployed, the public frontend can display the dashboard and prerecorded demo. The API-dependent camera registry, analytics and events require `API_URL` to point to an available FastAPI deployment. Map tiles come from OpenFreeMap's public service and therefore depend on that external service's availability; the local boundary GeoJSON is bundled with the app. This prototype has no authentication or role-based access control; it should not be exposed as an unrestricted operational safety service.

## F. Developer

**MADE BY JOE V KADAVAN**

GitHub: [https://github.com/Joevkadavan](https://github.com/Joevkadavan)  
Project repository: [https://github.com/Joevkadavan/gods-eye-dashboard](https://github.com/Joevkadavan/gods-eye-dashboard)

> The requested GitHub repository returned HTTP 404 to an unauthenticated public lookup at the time this document was written. No source has been published there yet; an authenticated GitHub connection is required to verify private-repository existence, create it if absent, and push the project.
