'use client';
import {useEffect,useMemo,useState} from 'react';
import {Activity,Camera,Car,ChevronDown,Gauge,TrendingDown,TrendingUp,Users} from 'lucide-react';
import {Area,AreaChart,CartesianGrid,ResponsiveContainer,Tooltip,XAxis,YAxis} from 'recharts';

type TrafficMetrics={people_count?:number;vehicle_count?:number;vehicle_box_occupancy_pct?:number;traffic_density_level?:'LOW'|'MODERATE'|'HIGH'|'VERY_HIGH';traffic_flow?:'MOVING'|'SLOW_MOVING'|'STATIONARY'|null;traffic_flow_tracks?:number;frame_width?:number;frame_height?:number};
type TrafficCamera={id:string;name:string;enabled:boolean;status:string;feed_kind?:string;city?:string|null};
type Sample={camera_id:string;timestamp:string;people_count:number;vehicle_count:number};
const DENSITY=[{key:'LOW',label:'Low',hint:'Low detected box occupancy'},{key:'MODERATE',label:'Moderate',hint:'Moderate detected box occupancy'},{key:'HIGH',label:'High',hint:'High detected box occupancy'},{key:'VERY_HIGH',label:'Very high',hint:'Very high detected box occupancy'}] as const;
const flowLabel=(flow?:string|null)=>flow==='MOVING'?'Moving':flow==='SLOW_MOVING'?'Slow Moving':flow==='STATIONARY'?'Stationary':'Insufficient data';
const densityLabel=(level?:string)=>DENSITY.find(x=>x.key===level)?.label||'—';
const statusFor=(camera:TrafficCamera|undefined,timestamp:string|undefined,now:number)=>{
 if(!camera||!camera.enabled||camera.status!=='online')return 'Unavailable';
 const age=timestamp?now-Date.parse(timestamp):Infinity;
 return Number.isFinite(age)&&age>=-60000&&age<=30000?'Processing':'Connected';
};
const clock=(stamp:string)=>new Date(stamp).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'});
const count=(n:number|undefined,usable:boolean)=>usable&&Number.isFinite(n)?String(n):'—';

export default function TrafficIntelligence({cameras,metrics,metricTimestamps,history,now}:{cameras:TrafficCamera[];metrics:Record<string,TrafficMetrics>;metricTimestamps:Record<string,string>;history:Sample[];now:number}){
 const [cameraId,setCameraId]=useState('');const [minutes,setMinutes]=useState(5);
 const videoCameras=useMemo(()=>cameras.filter(c=>c.feed_kind!=='image_refresh'),[cameras]);
 useEffect(()=>{if(!videoCameras.some(c=>c.id===cameraId))setCameraId(videoCameras[0]?.id||'')},[cameraId,videoCameras]);
 const selected=videoCameras.find(c=>c.id===cameraId);const metric=selected?metrics[selected.id]:undefined;const stamp=selected?metricTimestamps[selected.id]:undefined;
 const status=statusFor(selected,stamp,now);const current=status==='Processing';
 const metricHistory=useMemo(()=>history.filter(p=>p.camera_id===cameraId&&Number.isFinite(Date.parse(p.timestamp))).sort((a,b)=>Date.parse(a.timestamp)-Date.parse(b.timestamp)),[history,cameraId]);
 const points=useMemo(()=>{const cutoff=now-minutes*60*1000;return metricHistory.filter(p=>Date.parse(p.timestamp)>=cutoff&&Date.parse(p.timestamp)<=now+60000).map(p=>({timestamp:p.timestamp,time:clock(p.timestamp),vehicles:p.vehicle_count}))},[metricHistory,minutes,now]);
 const insights=useMemo(()=>{
  if(!selected||!metric||status!=='Processing')return [] as {text:string;kind:'up'|'down'|'steady'|'info'}[];
  const result:{text:string;kind:'up'|'down'|'steady'|'info'}[]=[];
  const prior=metricHistory.length>=2?metricHistory[metricHistory.length-2]:null;
  const latest=metricHistory.length?metricHistory[metricHistory.length-1]:null;
  if(prior&&latest&&Date.parse(latest.timestamp)>=now-60000&&Date.parse(latest.timestamp)-Date.parse(prior.timestamp)<=90000){
   const vehicleDelta=latest.vehicle_count-prior.vehicle_count;
   if(vehicleDelta>0)result.push({text:`Vehicle detections increased by ${vehicleDelta} since the previous stored sample.`,kind:'up'});
   else if(vehicleDelta<0)result.push({text:`Vehicle detections reduced by ${Math.abs(vehicleDelta)} since the previous stored sample.`,kind:'down'});
   const peopleDelta=latest.people_count-prior.people_count;
   if(peopleDelta>0)result.push({text:`Person-class detections increased by ${peopleDelta} since the previous stored sample.`,kind:'up'});
   else if(peopleDelta<0)result.push({text:`Person-class detections reduced by ${Math.abs(peopleDelta)} since the previous stored sample.`,kind:'down'});
  }
  if(metric.traffic_flow==='MOVING')result.push({text:`Tracked vehicle centers show movement in the current inference window (${metric.traffic_flow_tracks||0} track${metric.traffic_flow_tracks===1?'':'s'} measured).`,kind:'steady'});
  else if(metric.traffic_flow==='SLOW_MOVING')result.push({text:`Tracked vehicle centers show slow movement in the current inference window (${metric.traffic_flow_tracks||0} track${metric.traffic_flow_tracks===1?'':'s'} measured).`,kind:'info'});
  else if(metric.traffic_flow==='STATIONARY')result.push({text:`Measured vehicle tracks show little image-plane displacement in the current inference window.`,kind:'info'});
  if(metric.traffic_density_level==='HIGH'||metric.traffic_density_level==='VERY_HIGH')result.push({text:`Observed vehicle-box occupancy is ${densityLabel(metric.traffic_density_level).toLowerCase()} (${typeof metric.vehicle_box_occupancy_pct==='number'?`${metric.vehicle_box_occupancy_pct.toFixed(1)}% of frame area`:'current frame'}). This is a visual proxy, not road-capacity measurement.`,kind:'info'});
  return result.slice(0,4);
 },[selected,metric,metricHistory,status,now]);
 const usable=current&&!!metric;
 const trafficStatus=status==='Processing'?'PROCESSING':status==='Connected'?'CONNECTED':'UNAVAILABLE';
 const densityKey=usable?metric?.traffic_density_level:undefined;
 return <section className="traffic-intel" aria-labelledby="traffic-intel-title">
  <div className="traffic-intel-heading"><div><div className="eyebrow">CAMERA-BASED VIDEO METRICS</div><h2 id="traffic-intel-title">TRAFFIC FLOW &amp; CONGESTION INTELLIGENCE</h2><p>Observed detections and tracked-vehicle movement from the selected video source.</p></div><div className={`traffic-freshness ${current?'is-fresh':''}`}><i/>{selected?.feed_kind==='demo'?'SOURCE VIDEO ANALYTICS':current?'ANALYTICS UPDATING':'WAITING FOR FRESH ANALYTICS'}</div></div>
  <div className="traffic-selection-row"><label htmlFor="traffic-camera-select">Selected video camera</label><div className="traffic-select-wrap"><Camera size={14}/><select id="traffic-camera-select" value={cameraId} onChange={e=>setCameraId(e.target.value)} disabled={!videoCameras.length} aria-label="Select camera for traffic intelligence">{!videoCameras.length&&<option value="">No video cameras registered</option>}{videoCameras.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select><ChevronDown size={13}/></div>{selected&&<span className={`traffic-source-state ${status==='Unavailable'?'is-offline':''}`}>{trafficStatus}{selected.feed_kind==='demo'?' · NOT LIVE CCTV':''}</span>}</div>
  {!videoCameras.length?<div className="traffic-empty">No video analytics sources are registered. Image-refresh cameras are excluded because they are not continuous video and are not YOLO-processed.</div>:<>
   <div className="traffic-kpis">
    <article className="traffic-metric-card"><div className="traffic-metric-label"><Car size={14}/>VEHICLES DETECTED</div><div className="traffic-metric-value">{count(metric?.vehicle_count,usable)}</div><div className="traffic-metric-foot">Current selected-camera inference</div></article>
    <article className="traffic-metric-card"><div className="traffic-metric-label"><Users size={14}/>PEOPLE DETECTED</div><div className="traffic-metric-value">{count(metric?.people_count,usable)}</div><div className="traffic-metric-foot">Person-class detections; pedestrian behaviour is not classified</div></article>
    <article className="traffic-metric-card"><div className="traffic-metric-label"><Gauge size={14}/>TRAFFIC DENSITY</div><div className={`traffic-metric-value density-${densityKey?.toLowerCase().replace('_','-')||'unknown'}`}>{densityLabel(densityKey)}</div><div className="traffic-metric-foot">{usable&&typeof metric?.vehicle_box_occupancy_pct==='number'?`${metric.vehicle_box_occupancy_pct.toFixed(1)}% vehicle-box frame coverage`:'No fresh occupancy measurement'}</div></article>
    <article className="traffic-metric-card"><div className="traffic-metric-label"><Activity size={14}/>TRAFFIC FLOW</div><div className="traffic-metric-value">{usable?flowLabel(metric?.traffic_flow):'—'}</div><div className="traffic-metric-foot">{usable&&metric?.traffic_flow_tracks?`${metric.traffic_flow_tracks} measured vehicle track${metric.traffic_flow_tracks===1?'':'s'}`:'Needs recent vehicle-track observations'}</div></article>
    <article className="traffic-metric-card"><div className="traffic-metric-label"><Camera size={14}/>CAMERA STATUS</div><div className={`traffic-metric-value traffic-status-value status-${status.toLowerCase()}`}>{status}</div><div className="traffic-metric-foot">{stamp?`Last inference ${clock(stamp)}`:'No inference timestamp available'}</div></article>
   </div>
   <div className="traffic-content-grid">
    <article className="traffic-panel density-panel"><div className="traffic-panel-head"><div><h3>OBSERVED VEHICLE DENSITY</h3><p>Frame-space box-coverage proxy · not calibrated road capacity</p></div><span className={current?'traffic-live-tag':''}>{current?'UPDATING':'STALE / WAITING'}</span></div>
     <div className={`density-meter ${current?'density-meter-live':''}`} aria-label={`Observed density ${densityLabel(densityKey)}`}>
      <div className="density-rail">{DENSITY.map((level,i)=><div key={level.key} className={`density-segment segment-${level.key.toLowerCase().replace('_','-')} ${densityKey===level.key?'active':''}`}><span>{i+1}</span></div>)}</div>
      <div className="density-labels">{DENSITY.map(level=><div key={level.key} className={densityKey===level.key?'active':''}><b>{level.label}</b><small>{level.hint}</small></div>)}</div>
     </div>
     <div className="density-source-note">{usable?`Based on ${metric?.vehicle_count??0} actual vehicle detections${metric?.frame_width&&metric?.frame_height?` and ${metric.frame_width}×${metric.frame_height} frame geometry`:''}. Bands: &lt;2%, 2–&lt;5%, 5–&lt;10%, ≥10% box coverage.`:'The indicator stays inactive until a fresh video-inference sample is available.'}</div>
    </article>
    <article className="traffic-panel trend-panel"><div className="traffic-panel-head"><div><h3>VEHICLE DETECTIONS OVER TIME</h3><p>Persisted camera samples · actual timestamps only</p></div><div className="traffic-range" role="group" aria-label="Traffic chart time range">{[5,15,30].map(v=><button key={v} className={minutes===v?'active':''} aria-pressed={minutes===v} onClick={()=>setMinutes(v)}>{v}m</button>)}</div></div>
     <div className="traffic-trend-chart">{points.length>=2?<ResponsiveContainer width="100%" height="100%"><AreaChart data={points} margin={{top:10,right:12,bottom:0,left:-18}}><defs><linearGradient id="trafficVehicles" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#55d8d2" stopOpacity={.28}/><stop offset="95%" stopColor="#55d8d2" stopOpacity={0}/></linearGradient></defs><CartesianGrid stroke="#20303d" strokeDasharray="3 3" vertical={false}/><XAxis dataKey="time" tick={{fill:'#8da2af',fontSize:9}} axisLine={false} tickLine={false} minTickGap={24}/><YAxis allowDecimals={false} tick={{fill:'#8da2af',fontSize:9}} axisLine={false} tickLine={false}/><Tooltip labelFormatter={(_,payload)=>payload?.[0]?.payload?.timestamp?new Date(payload[0].payload.timestamp).toLocaleString():''} formatter={(value)=>[value,'Vehicle detections']} contentStyle={{background:'#0b141c',border:'1px solid #2a3b47',fontSize:10}}/><Area type="monotone" dataKey="vehicles" stroke="#55d8d2" fill="url(#trafficVehicles)" strokeWidth={2} dot={false} activeDot={{r:4,fill:'#8cead8',stroke:'#0b141c'}}/></AreaChart></ResponsiveContainer>:<div className="traffic-chart-empty"><Activity size={20}/><b>{metricHistory.length<2?'Collecting actual history':'No samples in this time range'}</b><span>{metricHistory.length<2?'At least two stored samples are needed to draw a trend. No placeholder points are added.':'Try a longer time window or wait for the next persisted video sample.'}</span></div>}</div>
    </article>
    <article className="traffic-panel camera-compare-panel"><div className="traffic-panel-head"><div><h3>CAMERA-WISE TRAFFIC COMPARISON</h3><p>Only registered video sources · select a row to inspect</p></div></div>
     {videoCameras.length?<div className="traffic-table-wrap"><table className="traffic-table"><thead><tr><th>Camera</th><th>Vehicles</th><th>Pedestrians*</th><th>Density</th><th>Flow</th><th>Status</th></tr></thead><tbody>{videoCameras.map(camera=>{const m=metrics[camera.id],s=statusFor(camera,metricTimestamps[camera.id],now),fresh=s==='Processing';return <tr key={camera.id} className={cameraId===camera.id?'selected':''} aria-selected={cameraId===camera.id} onClick={()=>setCameraId(camera.id)}><td><button className="traffic-camera-choice" aria-pressed={cameraId===camera.id} onClick={e=>{e.stopPropagation();setCameraId(camera.id)}}>{camera.name}</button></td><td>{count(m?.vehicle_count,fresh)}</td><td>{count(m?.people_count,fresh)}</td><td>{fresh?densityLabel(m?.traffic_density_level):'—'}</td><td>{fresh?flowLabel(m?.traffic_flow):'—'}</td><td><span className={`traffic-table-status status-${s.toLowerCase()}`}>{s}</span></td></tr>})}</tbody></table></div>:<div className="traffic-empty">No registered video cameras to compare.</div>}
     <div className="traffic-metric-foot">*Person-class detections; the model does not distinguish pedestrians from other people.</div>
    </article>
    <article className="traffic-panel insights-panel"><div className="traffic-panel-head"><div><h3>INTELLIGENCE INSIGHTS</h3><p>Observations only · no incident or threat predictions</p></div><Activity size={15}/></div>
     {insights.length?<ul className="traffic-insights">{insights.map((item,i)=><li key={`${cameraId}-${i}`} className={`insight-${item.kind}`}>{item.kind==='up'?<TrendingUp size={15}/>:item.kind==='down'?<TrendingDown size={15}/>:<Activity size={15}/>}<span>{item.text}</span></li>)}</ul>:<div className="traffic-chart-empty insights-empty"><span>{current?'Waiting for sufficient comparable observations to generate an insight.':'No fresh analytics available for an insight.'}</span></div>}
    </article>
   </div>
  </>}
 </section>
}
