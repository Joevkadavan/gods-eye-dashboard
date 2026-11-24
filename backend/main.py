"""GOD'S EYE local-first API and independent asynchronous camera workers."""
from __future__ import annotations
import asyncio, base64, json, logging, os, shutil, time, uuid, urllib.request, urllib.error
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent/".env")

import cv2
import numpy as np
import psutil
from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import desc, select, inspect, text

from cv_engine import YoloDetector, CameraState, draw_overlay, VEHICLE_IDS
from db import Base, Camera, CameraMetric, Event, SessionLocal, engine

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/"data"; MEDIA=DATA/"media"; UPLOADS=DATA/"uploads"; EVIDENCE=DATA/"evidence"
for p in (MEDIA,UPLOADS,EVIDENCE): p.mkdir(parents=True,exist_ok=True)
MODEL=Path(os.getenv("MODEL_PATH",str(Path(__file__).parent/"models/yolov8n.onnx")))
INFER_SIZE=int(os.getenv("INFER_SIZE","416")); CONF=float(os.getenv("DETECTION_CONFIDENCE","0.32"))
RETENTION_HOURS=int(os.getenv("RETENTION_HOURS","24")); MAX_CAMERAS=int(os.getenv("MAX_CAMERAS","6"))
CROWD_WARNING_COUNT=int(os.getenv("CROWD_WARNING_COUNT","15")); STATIONARY_SECONDS=int(os.getenv("STATIONARY_SECONDS","15"))
SETTINGS_FILE=DATA/"settings.json"
RUNTIME_SETTINGS={"inference_size":INFER_SIZE,"confidence_threshold":CONF,"retention_hours":RETENTION_HOURS,"max_cameras":MAX_CAMERAS,"crowd_warning_count":CROWD_WARNING_COUNT,"stationary_seconds":STATIONARY_SECONDS,"model":MODEL.name}
INDIAN_DEMO_ID="indian-urban-traffic-demo"
INDIAN_DEMO_FILE=MEDIA/"indian-urban-traffic-pexels-5009674.mp4"
INDIAN_DEMO_ATTRIBUTION="Pexels video 5009674 by Meenakshi Vinay Rai · India traffic (city not verified) · Pexels license: https://www.pexels.com/license/ · source: https://www.pexels.com/video/vehicles-on-the-road-in-india-5009674/"
demo_controls:dict[str,dict[str,Any]]={}
logging.basicConfig(level=os.getenv("LOG_LEVEL","INFO"),format="%(asctime)s %(levelname)s %(name)s %(message)s")
log=logging.getLogger("godseye.api")

class CameraIn(BaseModel):
    name:str=Field(min_length=1,max_length=120)
    source:str
    source_type:str="file"
    enabled:bool=True
class CameraPatch(BaseModel): enabled:bool|None=None; name:str|None=None
class VerifyIn(BaseModel): status:str; verified_by:str|None=None
class SettingsIn(BaseModel):
    inference_size:int=Field(ge=320,le=640)
    confidence_threshold:float=Field(ge=.05,le=.95)
    retention_hours:int=Field(ge=1,le=720)
    max_cameras:int=Field(ge=1,le=12)
    crowd_warning_count:int=Field(ge=3,le=200)
    stationary_seconds:int=Field(ge=5,le=600)
    model:str=Field(pattern=r"^yolov8n(\.int8)?\.onnx$")

class Hub:
    def __init__(self): self.clients:set[WebSocket]=set(); self.latest:dict[str,dict[str,Any]]={}; self.frames:dict[str,np.ndarray]={}; self.raw_frames:dict[str,np.ndarray]={}
    async def send(self,msg:dict[str,Any]):
        dead=[]
        for ws in list(self.clients):
            try: await ws.send_json(msg)
            except Exception: dead.append(ws)
        for ws in dead: self.clients.discard(ws)
hub=Hub(); states:dict[str,CameraState]={}; tasks:dict[str,asyncio.Task]={}; cap_lock=asyncio.Lock()
infer_lock=asyncio.Lock(); detector:YoloDetector|None=None


def iso_utc(value:datetime|None)->str|None:
    if value is None: return None
    if value.tzinfo is None: value=value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()

def serialize_camera(c:Camera)->dict[str,Any]:
    return {"id":c.id,"name":c.name,"source_type":c.source_type,"enabled":c.enabled,"status":c.status,
        "city":c.city,"state":c.state,"country":c.country,"latitude":c.latitude,"longitude":c.longitude,
        "feed_kind":c.feed_kind,"source_url":c.source_url,"attribution":c.attribution,
        "refresh_seconds":c.refresh_seconds,"last_checked_at":iso_utc(c.last_checked_at),
        "last_image_at":iso_utc(c.last_image_at),"health_message":c.health_message}
def serialize_event(e:Event)->dict[str,Any]: return {"id":e.id,"camera_id":e.camera_id,"category":e.category,"timestamp":e.timestamp.isoformat(),"confidence":e.confidence,"description":e.description,"severity":e.severity,"verification_status":e.verification_status,"evidence_url":f"/api/evidence/{Path(e.evidence_path).name}" if e.evidence_path else None}

async def read_frame(cap:cv2.VideoCapture):
    return await asyncio.to_thread(cap.read)

async def camera_worker(camera_id:str):
    global detector
    db=SessionLocal(); camera=db.get(Camera,camera_id)
    if not camera: db.close(); return
    source=camera.source; source_type=camera.source_type
    if source_type=="webcam": src=int(source)
    else: src=source
    cap=cv2.VideoCapture(src)
    cap.set(cv2.CAP_PROP_BUFFERSIZE,1)
    state=states.setdefault(camera_id,CameraState(camera_id))
    if not cap.isOpened():
        camera.status="offline"; camera.last_checked_at=datetime.now(timezone.utc); camera.health_message="Video source could not be opened; automatic reconnect is scheduled."
        db.commit(); db.close(); cap.release(); log.warning("camera %s could not open source",camera_id); return
    camera.status="online"; camera.last_checked_at=datetime.now(timezone.utc); camera.health_message="Video source opened; continuous frame processing active."
    db.commit(); db.close()
    last_event:dict[str,float]={}; last_frame_broadcast=0.; last_metric=0.; announced_online=False; consecutive_read_failures=0
    playback=demo_controls.setdefault(camera_id,{"paused":False,"position_ms":0.0,"duration_ms":max(0.0,cap.get(cv2.CAP_PROP_FRAME_COUNT)*1000/max(cap.get(cv2.CAP_PROP_FPS),1.0))})
    if source_type=="file":
        if playback.get("position_ms",0)>0:cap.set(cv2.CAP_PROP_POS_MSEC,float(playback["position_ms"]))
        playback["wall_started_at"]=time.monotonic();playback["wall_start_position_ms"]=float(cap.get(cv2.CAP_PROP_POS_MSEC))
    try:
        while True:
            db=SessionLocal(); camera=db.get(Camera,camera_id)
            if not camera or not camera.enabled: db.close(); break
            db.close()
            if source_type=="file":
                seek_to=playback.pop("seek_to_ms",None)
                if seek_to is not None:
                    cap.set(cv2.CAP_PROP_POS_MSEC,max(0.0,float(seek_to)))
                    playback["position_ms"]=float(cap.get(cv2.CAP_PROP_POS_MSEC));playback["wall_started_at"]=time.monotonic();playback["wall_start_position_ms"]=playback["position_ms"]
                    state=CameraState(camera_id);states[camera_id]=state
                    hub.frames.pop(camera_id,None);hub.raw_frames.pop(camera_id,None);hub.latest.pop(camera_id,None)
                if playback.get("paused"):
                    await asyncio.sleep(.05);continue
            ok,frame=await read_frame(cap)
            if not ok:
                if source_type=="file":
                    cap.set(cv2.CAP_PROP_POS_FRAMES,0);playback["position_ms"]=0.0;playback["wall_started_at"]=time.monotonic();playback["wall_start_position_ms"]=0.0
                    state=CameraState(camera_id);states[camera_id]=state
                    await asyncio.sleep(.05); continue
                hub.frames.pop(camera_id,None); hub.raw_frames.pop(camera_id,None); hub.latest.pop(camera_id,None)
                cdb=SessionLocal(); failed_cam=cdb.get(Camera,camera_id)
                if failed_cam and failed_cam.status!="offline":
                    failed_cam.status="offline"; failed_cam.last_checked_at=datetime.now(timezone.utc)
                    failed_cam.health_message="Video frames stopped; stale detections cleared and reconnection is being attempted."
                    cdb.commit()
                cdb.close(); consecutive_read_failures+=1
                if consecutive_read_failures>=5: break
                await asyncio.sleep(.1); continue
            consecutive_read_failures=0
            cdb=SessionLocal(); recovered=cdb.get(Camera,camera_id)
            if recovered and recovered.status!="online":
                recovered.status="online"; recovered.last_checked_at=datetime.now(timezone.utc)
                recovered.health_message="Video frames resumed; live inference processing has recovered."
                cdb.commit()
            cdb.close()
            now=time.time()
            if source_type=="file":
                media_position=float(cap.get(cv2.CAP_PROP_POS_MSEC));source_fps=max(float(cap.get(cv2.CAP_PROP_FPS)),1.0)
                target_position=float(playback.get("wall_start_position_ms",0.0))+(time.monotonic()-float(playback.get("wall_started_at",time.monotonic())))*1000
                # The CPU model may infer slower than a 25-fps source. Drop only
                # decoded frames that have fallen materially behind wall time so
                # the short demo keeps natural speed while still running real CV.
                if media_position+140.0 < target_position:continue
                playback["position_ms"]=media_position
            # Inference lock shares one session and caps CPU to one inference
            # at a time; independent feed workers continue grabbing latest frames.
            async with infer_lock:
                detections,latency=await asyncio.to_thread(detector.infer,frame)
            metrics,events=state.analyze(frame,detections,now,latency,crowd_warning_count=CROWD_WARNING_COUNT,stationary_seconds=STATIONARY_SECONDS)
            overlay=draw_overlay(frame,detections)
            hub.raw_frames[camera_id]=frame.copy()
            hub.frames[camera_id]=overlay
            payload={"type":"camera_update","camera_id":camera_id,"metrics":metrics,"detections":[{"bbox":d.bbox,"label":d.label,"class_id":d.class_id,"confidence":d.confidence,"track_id":d.track_id} for d in detections],"timestamp":datetime.now(timezone.utc).isoformat()}
            hub.latest[camera_id]=payload
            if not announced_online:
                # Demo playback is a source lifecycle transition, not a safety incident.
                # Keep informational camera-online events for authorized non-demo streams.
                if source_type!="file":
                    eid=str(uuid.uuid4()); evidence=EVIDENCE/f"{eid}.jpg"
                    cv2.imwrite(str(evidence),overlay,[cv2.IMWRITE_JPEG_QUALITY,82])
                    info=Event(id=eid,camera_id=camera_id,category="CAMERA_ONLINE",confidence=1.0,description="Authorised camera source is online and processing; operator acknowledgement required.",severity="INFORMATIONAL",verification_status="PENDING",evidence_path=str(evidence))
                    odb=SessionLocal(); odb.add(info); odb.commit(); odb.refresh(info); info_json=serialize_event(info); odb.close()
                    await hub.send({"type":"new_event","event":info_json})
                announced_online=True
            if now-last_metric>=10:
                mdb=SessionLocal()
                if mdb.get(Camera,camera_id):
                    mdb.add(CameraMetric(camera_id=camera_id,people_count=metrics["people_count"],vehicle_count=metrics["vehicle_count"],crowd_density=metrics["crowd_density_per_megapixel"],traffic_per_minute=metrics["vehicles_per_minute"],fps=metrics["fps"]))
                    mdb.commit()
                mdb.close(); last_metric=now
            if now-last_frame_broadcast>=.5:
                await hub.send(payload); last_frame_broadcast=now
            for ev in events:
                if now-last_event.get(ev["category"],0)<10: continue
                last_event[ev["category"]]=now
                eid=str(uuid.uuid4()); evidence=EVIDENCE/f"{eid}.jpg"
                cv2.imwrite(str(evidence),overlay,[cv2.IMWRITE_JPEG_QUALITY,82])
                item=Event(id=eid,camera_id=camera_id,category=ev["category"],confidence=float(ev["confidence"]),description=ev["description"],severity=ev["severity"],verification_status="PENDING",evidence_path=str(evidence))
                db=SessionLocal()
                if db.get(Camera,camera_id): db.add(item); db.commit(); db.refresh(item); event_json=serialize_event(item)
                else: event_json=None
                db.close()
                if event_json: await hub.send({"type":"new_event","event":event_json})
            await asyncio.sleep(.03)
    except asyncio.CancelledError: raise
    except Exception: log.exception("camera worker failed: %s",camera_id)
    finally:
        cap.release()
        db=SessionLocal(); c=db.get(Camera,camera_id)
        if c:
            c.status="offline"; c.last_checked_at=datetime.now(timezone.utc)
            c.health_message="Video worker stopped or connection lost; reconnect will be attempted while enabled."
            db.commit()
        db.close(); states.pop(camera_id,None); hub.frames.pop(camera_id,None); hub.raw_frames.pop(camera_id,None); hub.latest.pop(camera_id,None)
        if camera_id!=INDIAN_DEMO_ID: demo_controls.pop(camera_id,None)

async def camera_supervisor(camera_id:str):
    delay=2
    while True:
        db=SessionLocal(); camera=db.get(Camera,camera_id)
        if not camera or not camera.enabled or camera.source_type not in {"file","rtsp","webcam"}:
            db.close(); return
        db.close()
        await camera_worker(camera_id)
        db=SessionLocal(); camera=db.get(Camera,camera_id)
        should_retry=bool(camera and camera.enabled and camera.source_type in {"file","rtsp","webcam"})
        db.close()
        if not should_retry: return
        await asyncio.sleep(delay)
        delay=min(delay*2,30)

async def launch_camera(camera_id:str):
    if camera_id in tasks and not tasks[camera_id].done(): return
    tasks[camera_id]=asyncio.create_task(camera_supervisor(camera_id),name=f"camera:{camera_id}")

def prune_retained_data():
    cutoff=datetime.now(timezone.utc)-timedelta(hours=RETENTION_HOURS)
    db=SessionLocal()
    old=list(db.scalars(select(Event).where(Event.timestamp<cutoff)))
    old_metrics=list(db.scalars(select(CameraMetric).where(CameraMetric.timestamp<cutoff)))
    for metric in old_metrics: db.delete(metric)
    for e in old:
        if e.evidence_path: Path(e.evidence_path).unlink(missing_ok=True)
        db.delete(e)
    for path in UPLOADS.iterdir():
        try:
            if path.is_file() and datetime.fromtimestamp(path.stat().st_mtime,timezone.utc)<cutoff:
                # Expired uploaded video sources and their camera/event records
                cam=db.scalars(select(Camera).where(Camera.source==str(path))).first()
                if cam:
                    for ev in list(cam.events):
                        if ev.evidence_path: Path(ev.evidence_path).unlink(missing_ok=True)
                    db.delete(cam)  # relationships cascade associated events and metrics
                    if cam.id in tasks: tasks[cam.id].cancel()
                path.unlink(missing_ok=True)
        except OSError: log.exception("retention cleanup failed for %s",path)
    db.commit(); db.close()
    for p in EVIDENCE.glob("*.jpg"):
        try:
            if datetime.fromtimestamp(p.stat().st_mtime,timezone.utc)<cutoff: p.unlink(missing_ok=True)
        except OSError: log.exception("evidence expiry failed for %s",p)

async def retention_worker():
    while True:
        await asyncio.to_thread(prune_retained_data)
        await asyncio.sleep(1800)

INDIA_FEEDS=[
    {"id":"india-chennai-choolaimedu","name":"Choolaimedu High Road","city":"Chennai","state":"Tamil Nadu","country":"India","latitude":13.06372,"longitude":80.23031,"still_url":"https://opencctv.org/still/302297.jpg","embed_url":"https://opencctv.org/embed/302297","page_url":"https://opencctv.org/cameras/india/chennai-district/chennai/chennai-south-east-choolaimedu-high-road-302297","refresh_seconds":600},
    {"id":"india-chennai-tiruvottiyur","name":"Tiruvottiyur","city":"Chennai","state":"Tamil Nadu","country":"India","latitude":13.1923,"longitude":80.3157,"still_url":"https://opencctv.org/still/313940.jpg","embed_url":"https://opencctv.org/embed/313940","page_url":"https://opencctv.org/cameras/india/chennai-district/chennai/chennai-east-tiruvottiyur-313940","refresh_seconds":150},
]
CAMERA_COLUMNS={"city":"VARCHAR(80)","state":"VARCHAR(80)","country":"VARCHAR(80)","latitude":"FLOAT","longitude":"FLOAT","feed_kind":"VARCHAR(24) DEFAULT 'video'","source_url":"TEXT","attribution":"TEXT","refresh_seconds":"INTEGER","last_checked_at":"DATETIME","last_image_at":"DATETIME","health_message":"TEXT"}
def migrate_camera_columns():
    inspector=inspect(engine)
    if "cameras" not in inspector.get_table_names(): return
    existing={c["name"] for c in inspector.get_columns("cameras")}
    with engine.begin() as conn:
        for name,typ in CAMERA_COLUMNS.items():
            if name not in existing:
                if typ=="DATETIME" and engine.dialect.name=="postgresql": typ="TIMESTAMP WITH TIME ZONE"
                conn.execute(text(f"ALTER TABLE cameras ADD COLUMN {name} {typ}"))

def check_still_source(url:str):
    req=urllib.request.Request(url,headers={"User-Agent":"GODS-EYE-India-camera-health-check/1.0 (source attribution: OpenCCTV)","Accept":"image/jpeg,image/*;q=0.9","Cache-Control":"no-cache"})
    with urllib.request.urlopen(req,timeout=12) as response:
        content_type=response.headers.get("Content-Type","")
        sample=response.read(32)
        if response.status!=200 or not content_type.lower().startswith("image/") or not sample.startswith(b"\xff\xd8"):
            raise ValueError(f"Expected JPEG image, received HTTP {response.status} {content_type}")
        modified=response.headers.get("Last-Modified")
        parsed=None
        if modified:
            from email.utils import parsedate_to_datetime
            parsed=parsedate_to_datetime(modified)
        return parsed

async def image_refresh_worker(camera_id:str):
    while True:
        db=SessionLocal(); camera=db.get(Camera,camera_id)
        if not camera or not camera.enabled: db.close(); return
        source=camera.source; period=camera.refresh_seconds or 300
        db.close()
        try:
            image_at=await asyncio.to_thread(check_still_source,source)
            db=SessionLocal(); camera=db.get(Camera,camera_id)
            if not camera: db.close(); return
            camera.status="online"; camera.last_checked_at=datetime.now(timezone.utc)
            camera.last_image_at=image_at or camera.last_image_at; camera.health_message="Still image endpoint returned a valid JPEG; this feed is not continuous video."
            db.commit(); db.close()
        except Exception as exc:
            log.warning("image refresh source health check failed for %s: %s",camera_id,exc)
            db=SessionLocal(); camera=db.get(Camera,camera_id)
            if not camera: db.close(); return
            camera.status="offline"; camera.last_checked_at=datetime.now(timezone.utc); camera.health_message="Source check failed; image unavailable."
            db.commit(); db.close()
        await asyncio.sleep(max(60,min(period,600)))

@asynccontextmanager
async def lifespan(app:FastAPI):
    global detector, MODEL, INFER_SIZE, CONF, RETENTION_HOURS, MAX_CAMERAS, CROWD_WARNING_COUNT, STATIONARY_SECONDS, RUNTIME_SETTINGS
    Base.metadata.create_all(engine)
    migrate_camera_columns()
    if SETTINGS_FILE.exists():
        try:
            saved=json.loads(SETTINGS_FILE.read_text())
            if saved.get("inference_size") in {320,352,384,416,448,480,512,544,576,608,640} and saved.get("model") in {"yolov8n.onnx","yolov8n.int8.onnx"}:
                INFER_SIZE=int(saved["inference_size"]); CONF=float(saved["confidence_threshold"])
                RETENTION_HOURS=int(saved["retention_hours"]); MAX_CAMERAS=int(saved["max_cameras"])
                CROWD_WARNING_COUNT=int(saved["crowd_warning_count"]); STATIONARY_SECONDS=int(saved["stationary_seconds"]); MODEL=Path(__file__).parent/"models"/saved["model"]
                RUNTIME_SETTINGS={**RUNTIME_SETTINGS,**saved}
        except (ValueError,KeyError,TypeError): log.exception("invalid persisted settings; using environment defaults")
    if not MODEL.exists(): raise RuntimeError(f"Model file not found: {MODEL}")
    detector=YoloDetector(MODEL,INFER_SIZE,CONF,threads=int(os.getenv("ORT_THREADS","2")))
    prune_retained_data()
    retention_task=asyncio.create_task(retention_worker(),name="retention-cleanup")
    db=SessionLocal()
    # Remove only the bundled international demo-camera records and their generated
    # metrics/evidence; never relabel those clips as Indian feeds.
    bundled={str((MEDIA/name).resolve()) for name in ("person-bicycle-car-detection.mp4","one-by-one-person-detection.mp4","car-detection.mp4","store-aisle-detection.mp4")}
    for old_cam in list(db.scalars(select(Camera))):
        if old_cam.source in bundled:
            for ev in list(old_cam.events):
                if ev.evidence_path: Path(ev.evidence_path).unlink(missing_ok=True)
            db.delete(old_cam)  # SQLAlchemy relationships cascade event/metric cleanup.
    for feed in INDIA_FEEDS:
        cam=db.get(Camera,feed["id"])
        if not cam:
            cam=Camera(id=feed["id"],name=feed["name"],source=feed["still_url"],source_type="image_refresh",enabled=True,status="offline")
            db.add(cam)
        cam.name=feed["name"]; cam.source=feed["still_url"]; cam.source_type="image_refresh"
        cam.status="offline"; cam.city=feed["city"]; cam.state=feed["state"]; cam.country=feed["country"]; cam.latitude=feed["latitude"]; cam.longitude=feed["longitude"]
        cam.feed_kind="image_refresh"; cam.source_url=feed["embed_url"]
        cam.attribution=f"OpenCCTV embed · third-party operated · source page: {feed['page_url']}"
        cam.refresh_seconds=feed["refresh_seconds"]
    demo=db.get(Camera,INDIAN_DEMO_ID)
    if INDIAN_DEMO_FILE.exists():
        if demo is None:
            demo=Camera(id=INDIAN_DEMO_ID,name="GOD'S EYE – Indian Urban Traffic Demo",source=str(INDIAN_DEMO_FILE.resolve()),source_type="file",enabled=True,status="offline")
            db.add(demo)
        demo.name="GOD'S EYE – Indian Urban Traffic Demo";demo.source=str(INDIAN_DEMO_FILE.resolve());demo.source_type="file";demo.feed_kind="demo"
        demo.city=None;demo.state=None;demo.country="India";demo.latitude=None;demo.longitude=None
        demo.attribution=INDIAN_DEMO_ATTRIBUTION;demo.health_message="Prerecorded Pexels India traffic video; city not verified. DEMO, not live CCTV."
        for prior_event in demo.events:
            if prior_event.category=="CAMERA_ONLINE":
                prior_event.category="DEMO_PLAYBACK_STARTED"
                prior_event.description="Prerecorded demonstration video started; not a live CCTV connection."
    db.commit()
    feeds=list(db.scalars(select(Camera).where(Camera.enabled==True).order_by(Camera.name)))
    video_feeds=[]
    for cam in feeds:
        if cam.source_type=="image_refresh":
            if cam.id not in tasks or tasks[cam.id].done(): tasks[cam.id]=asyncio.create_task(image_refresh_worker(cam.id),name=f"image-refresh:{cam.id}")
        elif cam.source_type in {"file","rtsp","webcam"}:
            if cam.source_type=="file" and cam.feed_kind=="video": cam.feed_kind="demo"
            video_feeds.append(cam.id)
    db.commit()
    # Preserve the existing startup cap for video workers, while image-source
    # health checks run independently and do not consume inference capacity.
    startup_max=int(os.getenv("STARTUP_CAMERAS","2"))
    # Prioritize the self-contained labelled Indian demo in the startup worker budget.
    if INDIAN_DEMO_ID in video_feeds:video_feeds.remove(INDIAN_DEMO_ID);video_feeds.insert(0,INDIAN_DEMO_ID)
    for cid in video_feeds[:startup_max]: await launch_camera(cid)
    db.close()
    yield
    retention_task.cancel()
    for task in tasks.values(): task.cancel()
    await asyncio.gather(retention_task,*tasks.values(),return_exceptions=True)

app=FastAPI(title="GOD'S EYE API",version="0.1.0",description="Privacy-conscious, human-verified public-space video analytics prototype.",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])

@app.get("/api/health")
def health():
    vm=psutil.virtual_memory(); proc=psutil.Process()
    metadata=detector.session.get_modelmeta().custom_metadata_map if detector else {}
    providers=detector.session.get_providers() if detector else []
    device="CUDA / GPU" if any("CUDA" in p or "Tensorrt" in p for p in providers) else "CPU" if "CPUExecutionProvider" in providers else "Unknown"
    return {"status":"ok","model":MODEL.name,"model_version":metadata.get("version"),"model_architecture":metadata.get("description"),"model_metadata_date":metadata.get("date"),"model_status":"LOADED" if detector else "ERROR","input_resolution":INFER_SIZE,"runtime":"onnxruntime","active_workers":sum(not t.done() for t in tasks.values()),"providers":providers,"device":device,"cpu_provider":"CPUExecutionProvider" if "CPUExecutionProvider" in providers else None,"cpu_utilization_percent":psutil.cpu_percent(interval=None),"process_memory_mb":round(proc.memory_info().rss/1024**2,1),"system_memory_percent":vm.percent,"gpu_utilization_percent":None}

def is_review_alert(event:Any)->bool:
    """Pending, actionable safety cue; source lifecycle and demo events are not alerts."""
    return event.verification_status=="PENDING" and event.severity!="INFORMATIONAL" and not event.category.startswith("DEMO_")

def hourly_event_frequency(events:list[Any])->list[dict[str,Any]]:
    """Count real persisted events by UTC hour, with no synthetic empty buckets."""
    hourly={}
    for event in events:
        stamp=event.timestamp
        if stamp.tzinfo is None: stamp=stamp.replace(tzinfo=timezone.utc)
        bucket=stamp.astimezone(timezone.utc).replace(minute=0,second=0,microsecond=0)
        hourly[bucket]=hourly.get(bucket,0)+1
    return [{"timestamp":bucket.isoformat(),"count":count} for bucket,count in sorted(hourly.items())]

@app.get("/api/overview")
def overview():
    db=SessionLocal(); cams=list(db.scalars(select(Camera))); events=list(db.scalars(select(Event).order_by(desc(Event.timestamp)).limit(8))); pending_alerts=sum(is_review_alert(e) for e in db.scalars(select(Event).where(Event.verification_status=="PENDING"))); db.close()
    ms=[v.get("metrics",{}) for v in hub.latest.values()]
    vm=psutil.virtual_memory(); proc=psutil.Process()
    sys_metrics={"cpu_utilization_percent":psutil.cpu_percent(interval=None),"process_memory_mb":round(proc.memory_info().rss/1024**2,1),"system_memory_percent":vm.percent,"gpu_utilization_percent":None}
    video_cams=[c for c in cams if c.feed_kind!="image_refresh"]
    image_cams=[c for c in cams if c.feed_kind=="image_refresh"]
    return {"active_cameras":sum(c.status=="online" and c.enabled for c in video_cams),"total_cameras":len(video_cams),"available_image_sources":sum(c.status=="online" and c.enabled for c in image_cams),"total_image_sources":len(image_cams),"people_detected":sum(x.get("people_count",0) for x in ms),"vehicles_detected":sum(x.get("vehicle_count",0) for x in ms),"crowd_level":max((x.get("crowd_level","LOW") for x in ms),key=lambda x:{"LOW":0,"MODERATE":1,"HIGH":2}[x],default="LOW"),"active_alerts":pending_alerts,"fps":round(sum(x.get("fps",0) for x in ms),1),"system_metrics":sys_metrics,"system_health":"NOMINAL","cameras":[serialize_camera(c) for c in cams],"recent_events":[serialize_event(e) for e in events]}

@app.get("/api/cameras")
def list_cameras():
    db=SessionLocal(); out=[serialize_camera(c) for c in db.scalars(select(Camera))]; db.close(); return out

@app.get("/api/india-feeds")
def india_feeds():
    db=SessionLocal(); out=[serialize_camera(c) for c in db.scalars(select(Camera).where(Camera.country=="India").order_by(Camera.city,Camera.name))]; db.close(); return out

@app.post("/api/cameras")
async def add_camera(body:CameraIn):
    if body.source_type not in {"file","webcam","rtsp"}: raise HTTPException(400,"source_type must be file, webcam or rtsp; verified image-refresh sources are managed by the registry")
    if body.source_type=="file":
        p=Path(body.source).expanduser().resolve()
        allowed=[MEDIA.resolve(),UPLOADS.resolve()]
        if not any(p==a or a in p.parents for a in allowed) or not p.exists(): raise HTTPException(400,"File sources must be uploaded or placed in data/media")
        source=str(p)
    elif body.source_type=="webcam":
        try: source=str(int(body.source))
        except ValueError: raise HTTPException(400,"webcam source must be a device index")
    else:
        if not body.source.startswith("rtsp://"): raise HTTPException(400,"Only RTSP URLs accepted; use feeds you are authorised to access")
        source=body.source
    db=SessionLocal(); count=len(list(db.scalars(select(Camera))))
    if count>=MAX_CAMERAS: db.close(); raise HTTPException(409,f"Prototype limit is {MAX_CAMERAS} configured cameras")
    c=Camera(id=str(uuid.uuid4()),name=body.name,source=source,source_type=body.source_type,enabled=body.enabled,status="offline",feed_kind="demo" if body.source_type=="file" else "video")
    db.add(c); db.commit(); db.refresh(c); result=serialize_camera(c); db.close()
    if body.enabled: await launch_camera(c.id)
    return result

@app.post("/api/cameras/upload")
async def upload_video(file:UploadFile=File(...),name:str="Uploaded video"):
    if Path(file.filename or "").suffix.lower() not in {".mp4",".avi",".mov",".mkv"}: raise HTTPException(400,"Supported video formats: mp4, avi, mov, mkv")
    target=UPLOADS/f"{uuid.uuid4()}{Path(file.filename).suffix.lower()}"
    with target.open("wb") as f: shutil.copyfileobj(file.file,f)
    return await add_camera(CameraIn(name=name,source=str(target),source_type="file"))

@app.patch("/api/cameras/{camera_id}")
async def patch_camera(camera_id:str,body:CameraPatch):
    db=SessionLocal(); c=db.get(Camera,camera_id)
    if not c: db.close(); raise HTTPException(404,"Camera not found")
    if body.name is not None: c.name=body.name
    if body.enabled is not None: c.enabled=body.enabled
    enabled=c.enabled; db.commit(); result=serialize_camera(c); db.close()
    if not enabled and camera_id in tasks: tasks[camera_id].cancel()
    if enabled: await launch_camera(camera_id)
    return result

@app.delete("/api/cameras/{camera_id}")
async def delete_camera(camera_id:str):
    if camera_id in tasks: tasks[camera_id].cancel(); await asyncio.sleep(0)
    db=SessionLocal(); c=db.get(Camera,camera_id)
    if not c: db.close(); raise HTTPException(404,"Camera not found")
    for e in list(c.events):
        if e.evidence_path: Path(e.evidence_path).unlink(missing_ok=True)
    db.delete(c)  # relationships cascade associated events and metric rows
    db.commit(); db.close(); return {"deleted":camera_id}

@app.get("/api/events")
def list_events(severity:str|None=None,category:str|None=None,status:str|None=None,limit:int=100):
    db=SessionLocal(); q=select(Event).order_by(desc(Event.timestamp)).limit(min(max(limit,1),500))
    if severity: q=q.where(Event.severity==severity.upper())
    if category: q=q.where(Event.category==category.upper())
    if status: q=q.where(Event.verification_status==status.upper())
    out=[serialize_event(e) for e in db.scalars(q)]; db.close(); return out

@app.patch("/api/events/{event_id}/verify")
def verify_event(event_id:str,body:VerifyIn):
    if body.status not in {"ACKNOWLEDGED","VERIFIED","DISMISSED"}: raise HTTPException(400,"status must be ACKNOWLEDGED, VERIFIED or DISMISSED")
    db=SessionLocal(); e=db.get(Event,event_id)
    if not e: db.close(); raise HTTPException(404,"Event not found")
    e.verification_status=body.status; e.verified_by=body.verified_by; db.commit(); result=serialize_event(e); db.close(); return result

@app.get("/api/analytics")
def analytics():
    db=SessionLocal(); events=list(db.scalars(select(Event).order_by(desc(Event.timestamp)).limit(1000))); samples=list(db.scalars(select(CameraMetric).order_by(desc(CameraMetric.timestamp)).limit(3000))); db.close()
    distribution={}
    for e in events: distribution[e.category]=distribution.get(e.category,0)+1
    vehicle_classes={}
    for payload in hub.latest.values():
        for d in payload.get("detections",[]):
            if d.get("class_id") in VEHICLE_IDS:
                label=d.get("label","vehicle"); vehicle_classes[label]=vehicle_classes.get(label,0)+1
    event_frequency=hourly_event_frequency(events)
    return {"event_distribution":distribution,"vehicle_class_distribution":vehicle_classes,"event_frequency":[{"timestamp":e.timestamp.isoformat(),"category":e.category,"severity":e.severity} for e in reversed(events)],"event_frequency_buckets":event_frequency,"camera_metrics":hub.latest,"density_trend":[{"timestamp":m.timestamp.isoformat(),"camera_id":m.camera_id,"people_count":m.people_count,"vehicle_count":m.vehicle_count,"crowd_density_per_megapixel":m.crowd_density,"fps":m.fps,"vehicles_per_minute":m.traffic_per_minute} for m in reversed(samples)],"traffic":[{"camera_id":cid,"vehicles_per_minute":x.get("metrics",{}).get("vehicles_per_minute",0)} for cid,x in hub.latest.items()]}

@app.get("/api/cameras/{camera_id}/video")
def prerecorded_video(camera_id:str):
    """Serve only the bundled, licensed Indian traffic demo as seekable MP4."""
    if camera_id!=INDIAN_DEMO_ID:
        raise HTTPException(404,"No direct media file is available for this camera")
    if not INDIAN_DEMO_FILE.is_file():
        raise HTTPException(404,"Prerecorded demo media is unavailable")
    return FileResponse(str(INDIAN_DEMO_FILE),media_type="video/mp4",headers={"Cache-Control":"private, max-age=3600","Content-Disposition":"inline; filename=\"indian-urban-traffic-demo.mp4\""})

@app.get("/api/cameras/{camera_id}/telemetry")
def camera_telemetry(camera_id:str):
    """Lightweight actual YOLO payload + decoder position for the demo overlay."""
    payload=hub.latest.get(camera_id)
    if payload is None:
        raise HTTPException(404,"No current processed video telemetry is available")
    control=demo_controls.get(camera_id)
    return {"camera_id":camera_id,"timestamp":payload["timestamp"],"metrics":payload.get("metrics",{}),"detections":payload.get("detections",[]),"playback":{"prerecorded":control is not None,"paused":bool(control and control.get("paused")),"position_ms":control.get("position_ms") if control else None,"duration_ms":control.get("duration_ms") if control else None}}

@app.get("/api/cameras/{camera_id}/frame")
def synchronized_frame(camera_id:str,overlay:bool=True):
    """Return one JPEG and the exact detections/metrics produced from that frame."""
    payload=hub.latest.get(camera_id)
    frame=(hub.frames if overlay else hub.raw_frames).get(camera_id)
    if payload is None or frame is None:
        raise HTTPException(404,"No current processed video frame is available")
    ok,buf=cv2.imencode(".jpg",frame,[cv2.IMWRITE_JPEG_QUALITY,82])
    if not ok: raise HTTPException(500,"Could not encode processed frame")
    metrics=payload.get("metrics",{})
    playback=demo_controls.get(camera_id)
    return JSONResponse(content={"camera_id":camera_id,"timestamp":payload["timestamp"],"frame_base64":base64.b64encode(buf.tobytes()).decode("ascii"),"frame_width":metrics.get("frame_width"),"frame_height":metrics.get("frame_height"),"metrics":metrics,"detections":payload.get("detections",[]),"overlay":overlay,"model":MODEL.name,"model_status":"LOADED" if detector else "ERROR","playback":{"prerecorded":playback is not None,"paused":bool(playback and playback.get("paused")),"position_ms":playback.get("position_ms") if playback else None,"duration_ms":playback.get("duration_ms") if playback else None}},headers={"Cache-Control":"no-store"})

class PlaybackIn(BaseModel):
    action:str

@app.post("/api/cameras/{camera_id}/playback")
def control_playback(camera_id:str,body:PlaybackIn):
    if body.action not in {"play","pause","replay"}:raise HTTPException(400,"action must be play, pause or replay")
    db=SessionLocal();camera=db.get(Camera,camera_id);db.close()
    if not camera:raise HTTPException(404,"Camera not found")
    if camera.source_type!="file" or camera.feed_kind!="demo":raise HTTPException(400,"Playback controls are only supported for prerecorded demo files")
    control=demo_controls.get(camera_id)
    if control is None:raise HTTPException(409,"Demo video worker is not running")
    if body.action=="pause":
        if not control.get("paused"):control["paused_at"]=time.monotonic()
        control["paused"]=True
    elif body.action=="play":
        if control.get("paused_at") is not None and control.get("wall_started_at") is not None:
            control["wall_started_at"]+=time.monotonic()-control.pop("paused_at")
        control["paused"]=False
    else:
        control["paused"]=False;control.pop("paused_at",None);control["seek_to_ms"]=0.0
        control["position_ms"]=0.0;control["wall_start_position_ms"]=0.0;control["wall_started_at"]=time.monotonic()
        # Invalidate the previous decoded frame immediately. Never return the
        # pre-replay image/detections as though they came from the restarted clip.
        hub.frames.pop(camera_id,None);hub.raw_frames.pop(camera_id,None);hub.latest.pop(camera_id,None)
    return {"camera_id":camera_id,"action":body.action,"paused":control["paused"],"position_ms":control.get("position_ms",0.0),"duration_ms":control.get("duration_ms",0.0)}

@app.get("/api/cameras/{camera_id}/snapshot")
def snapshot(camera_id:str):
    frame=hub.frames.get(camera_id)
    if frame is None: raise HTTPException(404,"No live frame available")
    ok,buf=cv2.imencode(".jpg",frame)
    if not ok: raise HTTPException(500,"Could not encode frame")
    from fastapi.responses import Response
    return Response(content=buf.tobytes(),media_type="image/jpeg",headers={"Cache-Control":"no-store"})

@app.get("/api/evidence/{filename}")
def evidence(filename:str):
    if Path(filename).name!=filename: raise HTTPException(400,"Invalid path")
    p=EVIDENCE/filename
    if not p.exists(): raise HTTPException(404,"Evidence expired or not found")
    from fastapi.responses import FileResponse
    return FileResponse(p,media_type="image/jpeg",headers={"Cache-Control":"private, max-age=0"})

@app.websocket("/ws")
async def websocket(ws:WebSocket):
    await ws.accept(); hub.clients.add(ws)
    try:
        for payload in hub.latest.values(): await ws.send_json(payload)
        while True: await ws.receive_text()
    except WebSocketDisconnect: pass
    finally: hub.clients.discard(ws)

@app.get("/api/settings")
def settings(): return {**RUNTIME_SETTINGS,"model":MODEL.name,"privacy":"No face recognition, biometric inference or identity tracking; temporary camera-local track IDs.","human_verification_required":True,"external_authorities_auto_contact":False}

@app.put("/api/settings")
async def update_settings(body:SettingsIn):
    global INFER_SIZE, CONF, RETENTION_HOURS, MAX_CAMERAS, CROWD_WARNING_COUNT, STATIONARY_SECONDS, MODEL, detector, RUNTIME_SETTINGS
    if body.inference_size % 32: raise HTTPException(400,"inference_size must be divisible by 32")
    candidate=Path(__file__).parent/"models"/body.model
    if not candidate.exists(): raise HTTPException(400,"Requested model is not present on this installation")
    check_db=SessionLocal(); camera_count=len(list(check_db.scalars(select(Camera)))); check_db.close()
    if camera_count>body.max_cameras: raise HTTPException(409,"Remove cameras before lowering max_cameras")
    async with infer_lock:
        detector=YoloDetector(candidate,body.inference_size,body.confidence_threshold,threads=int(os.getenv("ORT_THREADS","2")))
        INFER_SIZE=body.inference_size; CONF=body.confidence_threshold; RETENTION_HOURS=body.retention_hours
        MAX_CAMERAS=body.max_cameras; CROWD_WARNING_COUNT=body.crowd_warning_count; STATIONARY_SECONDS=body.stationary_seconds; MODEL=candidate
        RUNTIME_SETTINGS=body.model_dump()
        SETTINGS_FILE.write_text(json.dumps(RUNTIME_SETTINGS,indent=2))
    return settings()

