"""Measure the already running local GOD'S EYE API for N seconds."""
import argparse,json,statistics,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def main():
 p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8000');p.add_argument('--seconds',type=int,default=20);a=p.parse_args();end=time.time()+a.seconds;rows=[]
 while time.time()<end:
  d=json.load(urllib.request.urlopen(a.url+'/api/overview',timeout=10));rows.append({'active_cameras':d['active_cameras'],'total_cameras':d['total_cameras'],'fps':d['fps'],'people':d['people_detected'],'vehicles':d['vehicles_detected'],'cpu':d['system_metrics']['cpu_utilization_percent'],'rss_mb':d['system_metrics']['process_memory_mb']});time.sleep(1)
 summary={'seconds_requested':a.seconds,'samples':len(rows),'active_camera_counts':sorted(set(r['active_cameras'] for r in rows)),'aggregate_fps_mean':round(statistics.mean(r['fps'] for r in rows),2),'aggregate_fps_min':round(min(r['fps'] for r in rows),2),'aggregate_fps_max':round(max(r['fps'] for r in rows),2),'cpu_percent_mean':round(statistics.mean(r['cpu'] for r in rows),1),'rss_mb_max':max(r['rss_mb'] for r in rows),'notes':'System CPU percentage is reported by psutil; GPU unavailable. Counts are per latest sampled frames, not ground-truth accuracy.'}
 out=ROOT/'data/evaluation/live_system_smoke.json';out.write_text(json.dumps({'summary':summary,'samples':rows},indent=2));print(json.dumps(summary,indent=2));print('wrote',out)
if __name__=='__main__':main()
