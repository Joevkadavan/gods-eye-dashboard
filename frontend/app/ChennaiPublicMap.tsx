'use client';
import {useEffect,useRef,useState} from 'react';
import type {Cam} from './traffic-types';

type Props={cameras:Cam[];selectedId:string;onSelect:(id:string)=>void};
type Geo={type:'FeatureCollection';features:Array<{type:'Feature';properties:{id:string;name:string;available:boolean};geometry:{type:'Point';coordinates:[number,number]}}>};
const emptyGeo:Geo={type:'FeatureCollection',features:[]};
export default function ChennaiPublicMap({cameras,selectedId,onSelect}:Props){
 const host=useRef<HTMLDivElement>(null),map=useRef<any>(null),geoRef=useRef<Geo>(emptyGeo),onSelectRef=useRef(onSelect);
 const [ready,setReady]=useState(false),[mapError,setMapError]=useState('');
 const geo:Geo={type:'FeatureCollection',features:cameras.filter(c=>Number.isFinite(c.longitude)&&Number.isFinite(c.latitude)).map(c=>({type:'Feature',properties:{id:c.id,name:c.name,available:c.status==='online'},geometry:{type:'Point',coordinates:[c.longitude as number,c.latitude as number]}}))};
 geoRef.current=geo;onSelectRef.current=onSelect;
 useEffect(()=>{let active=true;let instance:any;
  import('maplibre-gl').then(mod=>{
   if(!active||!host.current)return;
   const maplibre=(mod as any).default||mod;
   instance=new maplibre.Map({container:host.current,style:'https://tiles.openfreemap.org/styles/liberty',center:[80.2707,13.0827],zoom:10.2,minZoom:8,maxZoom:17,cooperativeGestures:true,scrollZoom:true,attributionControl:true});
   map.current=instance;
   instance.on('load',()=>{if(!active)return;
    instance.addSource('verified-chennai-sources',{type:'geojson',data:geoRef.current});
    instance.addLayer({id:'chennai-source-halos',type:'circle',source:'verified-chennai-sources',paint:{'circle-radius':['interpolate',['linear'],['zoom'],8,11,14,17],'circle-color':['case',['==',['get','available'],true],'#39d5a9','#ef7480'],'circle-opacity':.18,'circle-blur':.15}});
    instance.addLayer({id:'chennai-source-points',type:'circle',source:'verified-chennai-sources',paint:{'circle-radius':['interpolate',['linear'],['zoom'],8,5.5,14,8],'circle-color':['case',['==',['get','available'],true],'#32d6a5','#e66a78'],'circle-stroke-color':'#f0fffb','circle-stroke-width':2,'circle-opacity':1}});
    instance.addLayer({id:'chennai-source-labels',type:'symbol',source:'verified-chennai-sources',layout:{'text-field':['get','name'],'text-size':11,'text-offset':[0,1.25],'text-anchor':'top','text-optional':true},paint:{'text-color':'#f2fffc','text-halo-color':'#071117','text-halo-width':1.7}});
    instance.on('click','chennai-source-points',(event:any)=>{const id=event.features?.[0]?.properties?.id;if(id)onSelectRef.current(String(id))});
    instance.on('mouseenter','chennai-source-points',()=>instance.getCanvas().style.cursor='pointer');
    instance.on('mouseleave','chennai-source-points',()=>instance.getCanvas().style.cursor='');
    setReady(true);setMapError('');
   });
   instance.on('error',(event:any)=>{if(event?.error)setMapError('The street map could not load. Source status and camera details remain available below.')});
  }).catch(()=>{if(active)setMapError('The map could not load. Source status and camera details remain available below.')});
  return()=>{active=false;instance?.remove();map.current=null}
 },[]);
 useEffect(()=>{const source=map.current?.getSource('verified-chennai-sources');if(source)source.setData(geo as any)},[cameras,ready]);
 useEffect(()=>{const item=cameras.find(c=>c.id===selectedId);if(item&&map.current&&Number.isFinite(item.longitude)&&Number.isFinite(item.latitude))map.current.flyTo({center:[item.longitude,item.latitude],zoom:12.5,duration:450})},[selectedId,cameras]);
 return <div className="chennai-map-wrap">
  <div ref={host} className="chennai-map" role="region" aria-label="Interactive Chennai map. Markers show verified camera source locations; labels and the source list below provide the same information without using the map."/>
  {!ready&&!mapError&&<div className="chennai-map-loading" role="status">Loading Chennai map…</div>}
  {mapError&&<div className="chennai-map-warning" role="status">{mapError}</div>}
  <div className="chennai-map-legend" aria-label="Map marker legend"><span><i className="source-dot available"/>Source check succeeded</span><span><i className="source-dot unavailable"/>Source unavailable</span><small>Marker color describes source reachability only—not traffic speed or congestion.</small></div>
 </div>
}
