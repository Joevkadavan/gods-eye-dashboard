'use client';
import {useEffect,useState} from 'react';
export default function EyeLogo({size=34,active=true}:{size?:number;active?:boolean}){
 const [blink,setBlink]=useState(false);
 useEffect(()=>{if(!active)return;let timer:ReturnType<typeof setTimeout>;let alive=true;const schedule=()=>{timer=setTimeout(()=>{if(!alive)return;setBlink(true);setTimeout(()=>{if(alive)setBlink(false)},260);schedule()},3600+Math.random()*3700)};schedule();return()=>{alive=false;clearTimeout(timer)}},[active]);
 return <span className={`eye-logo ${active?'eye-logo-active':''} ${blink?'eye-blinking':''}`} style={{width:size,height:size}} aria-hidden="true"><svg viewBox="0 0 100 100" fill="none"><path d="M7 50C18 31 32 20 50 20s32 11 43 30C82 69 68 80 50 80S18 69 7 50Z" fill="#0b292b" stroke="#49dfcc" strokeWidth="3.6"/><g className="eye-iris"><circle cx="50" cy="50" r="21" fill="#0e4445" stroke="#67fff0" strokeWidth="2.2"/><circle cx="50" cy="50" r="14" fill="#117d78"/><circle className="eye-pupil" cx="50" cy="50" r="8" fill="#031011"/><circle className="eye-core-glint" cx="54" cy="46" r="3" fill="#e5fff9"/></g><path className="eye-lid eye-lid-top" d="M7 50C18 31 32 20 50 20s32 11 43 30" fill="#092024" stroke="#77fff0" strokeWidth="3"/><path className="eye-lid eye-lid-bottom" d="M7 50C18 69 32 80 50 80s32-11 43-30" fill="#092024" stroke="#77fff0" strokeWidth="3"/></svg></span>
}
