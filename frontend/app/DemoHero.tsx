'use client';
import {useCallback,useEffect,useRef,useState} from 'react';
import {Activity,Camera,Expand,LoaderCircle,Pause,Play,Volume2,VolumeX} from 'lucide-react';
import EyeLogo from './EyeLogo';

type HeroCamera={id:string;name:string;enabled:boolean;status:string;feed_kind?:string;attribution?:string|null};
type Detection={bbox:number[];label:string;class_id:number;confidence:number;track_id:number|null};
type Metrics={people_count:number;vehicle_count:number;fps:number;frame_width?:number;frame_height?:number};
type Telemetry={camera_id:string;timestamp:string;detections:Detection[];metrics:Metrics;playback?:{prerecorded:boolean;paused:boolean;position_ms:number|null;duration_ms:number|null}};
export default function DemoHero({camera,onOpenStation}:{camera:HeroCamera|null;onOpenStation:(id:string)=>void}){
 const root=useRef<HTMLElement>(null),video=useRef<HTMLVideoElement>(null),aligned=useRef(false);
 const [telemetry,setTelemetry]=useState<Telemetry|null>(null);const [synced,setSynced]=useState(false);const [playing,setPlaying]=useState(false);const [muted,setMuted]=useState(true);const [volume,setVolume]=useState(.72);const [buffering,setBuffering]=useState(true);const [mediaError,setMediaError]=useState('');const [controlNote,setControlNote]=useState('');
 const sourceUrl=camera?`/api/cameras/${encodeURIComponent(camera.id)}/video`:'';
 const sourcePage=camera?.attribution?.match(/source: (https?:\/\/\S+)/)?.[1]||null;
 const available=!!camera?.enabled&&camera.status==='online';
 useEffect(()=>{if(video.current){video.current.muted=muted;video.current.volume=volume}},[muted,volume]);
 useEffect(()=>{
  if(!camera){setTelemetry(null);setSynced(false);return}
  let active=true,timer:ReturnType<typeof setTimeout>|undefined;aligned.current=false;setTelemetry(null);setSynced(false);setControlNote('');
  const poll=async()=>{
   if(!active)return;
   try{
    const response=await fetch(`/api/cameras/${encodeURIComponent(camera.id)}/telemetry?t=${Date.now()}`,{cache:'no-store'});
    if(!response.ok){if(response.status!==404)setControlNote(`Analytics endpoint returned ${response.status}`);setSynced(false);timer=setTimeout(poll,600);return}
    const data:Telemetry=await response.json();if(!active)return;
    let alignedNow=false;const media=video.current;const position=data.playback?.position_ms;
    if(media&&media.readyState>=1&&Number.isFinite(position)){
     const target=Math.max(0,(position as number)/1000);const drift=media.currentTime-target;
     if(!aligned.current){media.currentTime=target;aligned.current=true;alignedNow=true}
     else if(Math.abs(drift)>0.95){media.currentTime=target;alignedNow=false}
     else alignedNow=Math.abs(drift)<=0.7;
    }
    setTelemetry(data);setSynced(alignedNow);
   }catch{if(active){setSynced(false);setControlNote('Analytics connection unavailable')}}
   if(active)timer=setTimeout(poll,450);
  };
  void poll();return()=>{active=false;if(timer)clearTimeout(timer)};
 },[camera?.id]);
 const runWorkerAction=useCallback(async(action:'play'|'pause'|'replay')=>{
  if(!camera)return;
  try{const r=await fetch(`/api/cameras/${encodeURIComponent(camera.id)}/playback`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action})});if(!r.ok)throw new Error((await r.json()).detail||`Playback ${action} failed`);setControlNote('')}
  catch(e){setControlNote(e instanceof Error?e.message:'Playback controls unavailable')}
 },[camera?.id]);
 const togglePlay=async()=>{const media=video.current;if(!media)return;if(media.paused){try{await media.play();setPlaying(true);void runWorkerAction('play')}catch{setMediaError('Tap play to start this video')}}else{media.pause();setPlaying(false);void runWorkerAction('pause')}};
 const replay=async()=>{if(video.current){video.current.currentTime=0;aligned.current=false;setSynced(false);try{await video.current.play();setPlaying(true)}catch{setMediaError('Tap play to restart this video')}}void runWorkerAction('replay')};
 const fullscreen=async()=>{try{if(document.fullscreenElement===root.current)await document.exitFullscreen();else await root.current?.requestFullscreen()}catch{setControlNote('Browser fullscreen is unavailable for this viewer')}};
 const m=telemetry?.metrics;const width=m?.frame_width,height=m?.frame_height;
 const showBoxes=!!telemetry&&synced&&!!width&&!!height&&available;
 const statusText=!camera?'Loading demo source…':mediaError?'VIDEO UNAVAILABLE':buffering?'BUFFERING':playing?'PLAYING':'PAUSED';
 return <section className="demo-hero" ref={root} aria-label="GOD’S EYE Indian Urban Traffic prerecorded demonstration video">
  <div className="demo-video-stage">
   {camera?<video ref={video} className="demo-video" src={sourceUrl} autoPlay muted loop playsInline preload="auto" aria-label="Prerecorded Indian Urban Traffic demonstration video" onPlay={()=>{setPlaying(true);setBuffering(false)}} onPause={()=>setPlaying(false)} onWaiting={()=>setBuffering(true)} onPlaying={()=>setBuffering(false)} onCanPlay={()=>setBuffering(false)} onError={()=>{setMediaError('The bundled demo video could not be loaded');setBuffering(false)}}/>:<div className="demo-video-placeholder"><LoaderCircle size={24}/><span>Loading the registered prerecorded demo source…</span></div>}
   {showBoxes&&<svg className="demo-detection-overlay" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="xMidYMid meet" aria-label="Current synchronized YOLO detections">{telemetry!.detections.map((d,i)=>{const [x1,y1,x2,y2]=d.bbox;if(![x1,y1,x2,y2].every(Number.isFinite))return null;const label=`${d.label} ${(d.confidence*100).toFixed(0)}%`;const fs=Math.max(15,(width||1280)*.009);return <g key={`${d.track_id??'x'}-${d.class_id}-${i}`}><rect x={x1} y={y1} width={Math.max(0,x2-x1)} height={Math.max(0,y2-y1)} fill="none" stroke="#52f4d7" strokeWidth={Math.max(2,(width||1280)*.0018)}/><rect x={x1} y={Math.max(0,y1-fs*1.7)} width={label.length*fs*.56} height={fs*1.55} rx={3} fill="#06231ee8"/><text x={x1+fs*.3} y={Math.max(fs,y1-fs*.48)} fill="#dffff7" fontSize={fs} fontFamily="Arial, sans-serif">{label}</text></g>})}</svg>}
   {buffering&&!mediaError&&camera&&<div className="demo-buffer-state" role="status"><LoaderCircle size={25}/><span>BUFFERING PRERECORDED VIDEO</span></div>}
   {!camera&&<div className="demo-buffer-state" role="status"><LoaderCircle size={25}/><span>WAITING FOR DEMO CAMERA REGISTRY</span></div>}
   {mediaError&&<div className="demo-buffer-state demo-media-error" role="status"><Camera size={24}/><b>{mediaError}</b>{sourcePage&&<a href={sourcePage} target="_blank" rel="noreferrer">Open the attributed source ↗</a>}</div>}
   <div className="demo-hero-shade"/>
   <div className="demo-hero-top"><div className="demo-hero-brand"><span className="demo-hero-eye"><EyeLogo size={34}/></span><span><b>GOD’S EYE</b><small>INDIAN URBAN TRAFFIC <i/> INDIA · CITY NOT VERIFIED</small></span></div><div className="demo-hero-status"><span className={`demo-source-state ${available?'available':'unavailable'}`}><i/>{available?'SOURCE AVAILABLE':'SOURCE UNAVAILABLE'}</span><span className={`demo-play-state ${playing?'playing':''}`}><i/>{statusText}</span><button className="demo-fullscreen" onClick={fullscreen} aria-label="Fullscreen video" title="Fullscreen video"><Expand size={17}/></button></div></div>
   <div className="demo-hero-bottom"><div className="demo-kpis"><div><span>PEOPLE DETECTED</span><b>{m?.people_count??'—'}</b></div><div><span>VEHICLES DETECTED</span><b>{m?.vehicle_count??'—'}</b></div><div><span>INFERENCE FPS</span><b>{typeof m?.fps==='number'?m.fps.toFixed(1):'—'}</b></div><div className={`demo-analytics-state ${synced?'synced':''}`}><span>ANALYTICS STATUS</span><b><Activity size={13}/>{synced?'YOLO FRAME SYNCED':available?'SYNCING YOLO FRAME':'ANALYTICS OFFLINE'}</b></div></div>
    <div className="demo-player-controls"><button onClick={togglePlay} disabled={!camera||!!mediaError} aria-label={playing?'Pause video':'Play video'} title={playing?'Pause':'Play'}>{playing?<Pause size={17}/>:<Play size={17}/>}</button><button onClick={replay} disabled={!camera||!!mediaError} aria-label="Restart video" title="Restart demo">↺</button><button onClick={()=>setMuted(v=>!v)} aria-label={muted?'Unmute video':'Mute video'} title={muted?'Unmute':'Mute'}>{muted?<VolumeX size={17}/>:<Volume2 size={17}/>}</button><input className="demo-volume" type="range" min="0" max="1" step=".05" value={volume} aria-label="Video volume" onChange={e=>{const next=Number(e.target.value);setVolume(next);setMuted(next===0)}}/><span className="demo-audio-note">{muted?'MUTED · AUTOPLAY':'AUDIO ON'}</span><button className="demo-open-station" onClick={()=>camera&&onOpenStation(camera.id)} disabled={!camera}><Camera size={14}/> OPEN YOLO STATION</button></div>
    <div className="demo-credit-line">PRERECORDED PEXELS VIDEO · NOT LIVE CCTV · {telemetry?`PROCESSED ${new Date(telemetry.timestamp).toLocaleTimeString()}`:'WAITING FOR YOLO DATA'}{controlNote&&<span className="demo-control-note"> · {controlNote}</span>}{sourcePage&&<a href={sourcePage} target="_blank" rel="noreferrer"> SOURCE ↗</a>}</div>
   </div>
  </div>
 </section>
}
