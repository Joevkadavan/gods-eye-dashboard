'use client';
import type {PointerEvent,WheelEvent} from 'react';
import {useEffect,useMemo,useRef,useState} from 'react';
import {Camera,LocateFixed,RotateCcw,ZoomIn,ZoomOut} from 'lucide-react';

type Cam={id:string;name:string;status:string;city?:string|null;state?:string|null;country?:string|null;latitude?:number|null;longitude?:number|null;feed_kind?:string;last_checked_at?:string|null;last_image_at?:string|null};
type Metric=Record<string,number|string|null|undefined>;
type StateShape={name:string;iso:string;d:string};
type Pan={x:number;y:number;scale:number};
const VIEW={w:900,h:990},LON0=67,LAT0=37.5,SX=28,SY=30;
const CITIES=[['New Delhi',77.209,28.614],['Mumbai',72.878,19.076],['Chennai',80.2707,13.0827],['Kolkata',88.3639,22.5726],['Bengaluru',77.5946,12.9716],['Hyderabad',78.4867,17.385],['Ahmedabad',72.5714,23.0225],['Jaipur',75.7873,26.9124],['Lucknow',80.9462,26.8467],['Guwahati',91.7362,26.1445]] as const;
const xy=(lon:number,lat:number)=>({x:(lon-LON0)*SX,y:(LAT0-lat)*SY});
const clamp=(n:number,min:number,max:number)=>Math.max(min,Math.min(max,n));
const dateText=(stamp?:string|null)=>stamp&&Number.isFinite(Date.parse(stamp))?new Date(stamp).toLocaleString('en-IN',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'}):'Not recorded';
const fresh=(stamp?:string)=>!!stamp&&Date.now()-Date.parse(stamp)>=-60000&&Date.now()-Date.parse(stamp)<=30000;
export default function FastIndiaMap({cameras,onOpenCamera,metrics={},metricTimestamps={}}:{cameras:Cam[];onOpenCamera:(id:string)=>void;metrics?:Record<string,Metric>;metricTimestamps?:Record<string,string>}){
 const [shapes,setShapes]=useState<StateShape[]>([]),[svgData,setSvgData]=useState(''),[shapeError,setShapeError]=useState(''),[filter,setFilter]=useState('ALL'),[selectedId,setSelectedId]=useState(''),[selectedState,setSelectedState]=useState(''),[hoveredId,setHoveredId]=useState(''),[hoveredState,setHoveredState]=useState(''),[pan,setPan]=useState<Pan>({x:0,y:0,scale:1}),[city,setCity]=useState('');
 const svgRef=useRef<SVGSVGElement>(null),drag=useRef<{id:number;x:number;y:number;tx:number;ty:number;moved:boolean}|null>(null);
 const valid=useMemo(()=>cameras.filter(c=>Number.isFinite(c.latitude)&&Number.isFinite(c.longitude)&&c.latitude!>=5&&c.latitude!<=38&&c.longitude!>=67&&c.longitude!<=99),[cameras]);
 const shown=useMemo(()=>valid.filter(c=>filter==='ALL'||(filter==='AVAILABLE'&&c.status==='online')||(filter==='UNAVAILABLE'&&c.status!=='online')),[valid,filter]);
 const selected=valid.find(c=>c.id===selectedId)||null;
 const selectedMetric=selected?metrics[selected.id]:undefined;const current=selected?fresh(metricTimestamps[selected.id]):false;
 useEffect(()=>{let active=true;fetch('/data/india_states.svg',{cache:'force-cache'}).then(r=>{if(!r.ok)throw new Error('Local India SVG unavailable');return r.text()}).then(text=>{if(!active)return;const doc=new DOMParser().parseFromString(text,'image/svg+xml');const paths=[...doc.querySelectorAll('path[data-name]')].map(p=>({name:p.getAttribute('data-name')||'State / UT',iso:p.getAttribute('data-iso')||'',d:p.getAttribute('d')||''})).filter(p=>p.d);if(!paths.length)throw new Error('India boundary paths were empty');setShapes(paths);setSvgData(`data:image/svg+xml;charset=utf-8,${encodeURIComponent(text)}`)}).catch(e=>{if(active)setShapeError(e instanceof Error?e.message:'Local state boundary data unavailable')});return()=>{active=false}},[]);
 useEffect(()=>{if(selectedId&&!valid.some(c=>c.id===selectedId))setSelectedId('')},[valid,selectedId]);
 const bound=(next:Pan):Pan=>{const s=clamp(next.scale,1,8);return {scale:s,x:clamp(next.x,VIEW.w*(1-s),0),y:clamp(next.y,VIEW.h*(1-s),0)}};
 const centerAt=(lon:number,lat:number,scale=2.2)=>{const p=xy(lon,lat);setPan(bound({scale,x:VIEW.w/2-p.x*scale,y:VIEW.h/2-p.y*scale}))};
 const zoomAt=(x:number,y:number,factor:number)=>setPan(old=>{const s=clamp(old.scale*factor,1,8),ratio=s/old.scale;return bound({scale:s,x:x-(x-old.x)*ratio,y:y-(y-old.y)*ratio})});
 const toSvg=(clientX:number,clientY:number)=>{const r=svgRef.current?.getBoundingClientRect();return r?{x:(clientX-r.left)*VIEW.w/r.width,y:(clientY-r.top)*VIEW.h/r.height}:{x:VIEW.w/2,y:VIEW.h/2}};
 const startPan=(e:PointerEvent<SVGSVGElement>)=>{if(e.button!==0)return;drag.current={id:e.pointerId,x:e.clientX,y:e.clientY,tx:pan.x,ty:pan.y,moved:false};e.currentTarget.setPointerCapture(e.pointerId)};
 const movePan=(e:PointerEvent<SVGSVGElement>)=>{const d=drag.current;if(!d||d.id!==e.pointerId)return;const r=e.currentTarget.getBoundingClientRect(),dx=(e.clientX-d.x)*VIEW.w/r.width,dy=(e.clientY-d.y)*VIEW.h/r.height;if(Math.abs(dx)+Math.abs(dy)>3)d.moved=true;if(d.moved)setPan(old=>bound({...old,x:d.tx+dx,y:d.ty+dy}))};
 const endPan=(e:PointerEvent<SVGSVGElement>)=>{if(drag.current?.id===e.pointerId)drag.current=null};
 const wheel=(e:WheelEvent<SVGSVGElement>)=>{e.preventDefault();const p=toSvg(e.clientX,e.clientY);zoomAt(p.x,p.y,e.deltaY<0?1.18:1/1.18)};
 const selectCamera=(c:Cam)=>{setSelectedId(c.id);setSelectedState('');setCity('');if(Number.isFinite(c.longitude)&&Number.isFinite(c.latitude))centerAt(c.longitude!,c.latitude!,Math.max(2.4,pan.scale))};
 const reset=()=>{setPan({x:0,y:0,scale:1});setSelectedId('');setSelectedState('');setCity('')};
 const cityChange=(name:string)=>{setCity(name);setSelectedId('');setSelectedState('');if(!name){setPan({x:0,y:0,scale:1});return}const c=CITIES.find(c=>c[0]===name);if(c)centerAt(c[1],c[2],2.6)};
 const availableCount=valid.filter(c=>c.status==='online').length;
 return <div className="fast-map-shell">
  <div className="fast-map-tools"><label>State / UT <select value={selectedState} onChange={e=>{setSelectedState(e.target.value);setSelectedId('')}}><option value="">All India</option>{shapes.map(s=><option key={s.iso||s.name} value={s.name}>{s.name}</option>)}</select></label><label>Navigate to city <select value={city} onChange={e=>cityChange(e.target.value)}><option value="">India overview</option>{CITIES.map(c=><option key={c[0]} value={c[0]}>{c[0]}</option>)}</select></label><label>Camera sources <select value={filter} onChange={e=>setFilter(e.target.value)}><option value="ALL">All registered</option><option value="AVAILABLE">Available</option><option value="UNAVAILABLE">Unavailable</option></select></label><div className="fast-map-actions"><button className="btn" aria-label="Zoom in" onClick={()=>zoomAt(450,495,1.25)}><ZoomIn size={13}/></button><button className="btn" aria-label="Zoom out" onClick={()=>zoomAt(450,495,1/1.25)}><ZoomOut size={13}/></button><button className="btn" onClick={reset}><RotateCcw size={12}/> Reset</button></div></div>
  <div className="fast-map-frame"><div className="fast-map-canvas">
   <svg ref={svgRef} className="fast-india-svg" viewBox={`0 0 ${VIEW.w} ${VIEW.h}`} role="img" aria-label="Interactive local India state and union territory map with camera markers" onPointerDown={startPan} onPointerMove={movePan} onPointerUp={endPan} onPointerCancel={endPan} onWheel={wheel}>
    <g transform={`translate(${pan.x} ${pan.y}) scale(${pan.scale})`}>
     {svgData&&<image href={svgData} x="0" y="0" width={VIEW.w} height={VIEW.h} preserveAspectRatio="none" className="fast-map-image"/>}
     {shapes.map(s=><path key={s.iso||s.name} d={s.d} className={`fast-state-hit ${selectedState===s.name?'selected':''}`} onPointerDown={e=>e.stopPropagation()} onClick={e=>{e.stopPropagation();setSelectedState(s.name);setSelectedId('');setHoveredState('')}} onPointerEnter={()=>setHoveredState(s.name)} onPointerLeave={()=>setHoveredState('')} aria-label={`Select ${s.name}`}><title>{s.name}</title></path>)}
     {shown.map(c=>{const p=xy(c.longitude!,c.latitude!);const isActive=c.status==='online';const highlight=hoveredId===c.id||selectedId===c.id;return <g key={c.id} transform={`translate(${p.x} ${p.y})`} className="fast-camera-marker" onPointerDown={e=>e.stopPropagation()} onPointerEnter={()=>setHoveredId(c.id)} onPointerLeave={()=>setHoveredId(id=>id===c.id?'':id)} onClick={e=>{e.stopPropagation();selectCamera(c)}} role="button" tabIndex={0} aria-label={`${c.name}, ${c.city||c.state||'India'}, source ${isActive?'available':'unavailable'}`} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();selectCamera(c)}}}>
      <circle r={highlight?10:7} className={`fast-camera-halo ${isActive?'available':'unavailable'}`}/><circle r={4.2} className={`fast-camera-dot ${isActive?'available':'unavailable'}`}/><title>{c.name} · {c.city||c.state||'India'} · {isActive?'Source available':'Source unavailable'}</title>
      {highlight&&<g className="fast-marker-label"><rect x="10" y="-25" width={Math.min(220,Math.max(95,c.name.length*6+18))} height="22" rx="4"/><text x="17" y="-10">{c.name}</text></g>}
     </g>})}
    </g>
   </svg>
   <div className="fast-map-caption"><LocateFixed size={12}/>{selectedState||hoveredState||(svgData?'India · State / UT boundaries':'Loading local India boundaries…')}<span>{shown.length} cameras · {availableCount} available</span></div>
   {shapeError&&<div className="fast-map-note" role="status">Showing local India map image; state selection could not be enabled: {shapeError}</div>}
  </div></div>
  <div className="map-legend"><span><i className="map-dot available"/> Source available</span><span><i className="map-dot unavailable"/> Source unavailable</span><span>Hover or select a marker for its name · drag to pan · scroll / buttons to zoom</span></div>
  {selected&&<div className="map-selected"><div className="map-selected-icon"><Camera size={15}/></div><div className="fast-selected-copy"><b>{selected.name}</b><div className="tiny">{[selected.city,selected.state].filter(Boolean).join(', ')||'Location metadata unavailable'} · {selected.latitude?.toFixed(5)}, {selected.longitude?.toFixed(5)}</div><div className="tiny">{selected.status==='online'?'Source available':'Source unavailable'} · {selected.feed_kind==='image_refresh'?'Periodic still-image source':selected.feed_kind==='demo'?'Traffic video · not live CCTV':'Video source'} · last checked {dateText(selected.last_checked_at)}</div>
    {selected.feed_kind!=='image_refresh'&&<div className="fast-analytics">{current&&selectedMetric?<><span>People <b>{selectedMetric.people_count??'—'}</b></span><span>Vehicles <b>{selectedMetric.vehicle_count??'—'}</b></span><span>Flow <b>{typeof selectedMetric.traffic_flow==='string'?selectedMetric.traffic_flow.replaceAll('_',' '):'—'}</b></span><small>Analytics timestamp {dateText(metricTimestamps[selected.id])}</small></>:<small>{selected.feed_kind==='demo'?'Waiting for current video analytics.':'No fresh video analytics available.'}</small>}</div>}
    {selected.feed_kind==='image_refresh'&&<div className="fast-analytics"><small>Still-image sources are not computer-vision processed.</small></div>}
   </div><button className="btn primary map-open-camera" onClick={()=>onOpenCamera(selected.id)}><Camera size={13}/> Open Camera</button><button className="btn" onClick={()=>setSelectedId('')} aria-label="Close selected source">×</button></div>}
  <div className="footer-note">Local state / UT reference boundaries: geoBoundaries gbOpen India ADM1, simplified for display, CC BY 4.0; not a legal boundary. Camera markers use only registered coordinates. The fast map and source visibility do not depend on external tiles.</div>
 </div>
}
