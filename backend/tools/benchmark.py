"""Reproducible inference benchmark on the bundled demo clips (no labels).

Run from backend/: python tools/benchmark.py --frames-per-clip 20
Outputs data/evaluation/model_benchmark.csv and .json. These are runtime
measurements only; they do NOT establish detection precision/recall/mAP.
"""
from __future__ import annotations
import argparse, csv, json, statistics, time
from pathlib import Path
import cv2, numpy as np, onnxruntime as ort, psutil

ROOT=Path(__file__).resolve().parents[2]
MODELS=Path(__file__).resolve().parents[1]/"models"
VIDEOS=ROOT/"data"/"media"
OUT=ROOT/"data"/"evaluation"

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--frames-per-clip',type=int,default=20);args=ap.parse_args()
    variants=[('fp32','yolov8n.onnx'),('int8-weight-only','yolov8n.int8.onnx')]
    rows=[];proc=psutil.Process()
    for variant,filename in variants:
        model=MODELS/filename
        if not model.exists(): continue
        for size in (320,416,640):
            so=ort.SessionOptions();so.intra_op_num_threads=2;so.inter_op_num_threads=1;so.graph_optimization_level=ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            sess=ort.InferenceSession(str(model),sess_options=so,providers=['CPUExecutionProvider']);iname=sess.get_inputs()[0].name
            frames=[];per_clip={}
            for path in sorted(VIDEOS.glob('*.mp4')):
                cap=cv2.VideoCapture(str(path));arr=[]
                for _ in range(args.frames_per_clip):
                    ok,f=cap.read()
                    if not ok:break
                    arr.append(f)
                cap.release();per_clip[path.name]=arr;frames.extend(arr)
            def tensor(frame):
                h,w=frame.shape[:2];scale=min(size/w,size/h);nw,nh=round(w*scale),round(h*scale)
                resized=cv2.resize(frame,(nw,nh));canvas=np.full((size,size,3),114,np.uint8);px=(size-nw)//2;py=(size-nh)//2;canvas[py:py+nh,px:px+nw]=resized
                return cv2.dnn.blobFromImage(canvas,1/255,(size,size),swapRB=True)
            if not frames:continue
            warm=tensor(frames[0])
            for _ in range(3):sess.run(None,{iname:warm})
            lat=[];detections=0;proc.cpu_percent(None);system_before=psutil.cpu_percent(None)
            start=time.perf_counter()
            for frame in frames:
                blob=tensor(frame);t0=time.perf_counter();out=sess.run(None,{iname:blob})[0][0].T;lat.append((time.perf_counter()-t0)*1000)
                scores=out[:,4:].max(axis=1);detections+=int((scores>=.32).sum())
            elapsed=time.perf_counter()-start
            cpu_proc=proc.cpu_percent(None);cpu_system=psutil.cpu_percent(None);rss=proc.memory_info().rss/1024**2
            row={'variant':variant,'model_file':filename,'input_size':size,'frames':len(frames),'total_wall_seconds':round(elapsed,3),'throughput_fps':round(len(frames)/elapsed,2),'latency_mean_ms':round(statistics.mean(lat),2),'latency_p50_ms':round(float(np.percentile(lat,50)),2),'latency_p95_ms':round(float(np.percentile(lat,95)),2),'process_cpu_percent':round(cpu_proc,1),'system_cpu_percent_sample':round(cpu_system,1),'process_rss_mb':round(rss,1),'confidence_threshold':.32,'detections_above_threshold_unlabelled':detections,'gpu_utilization_percent':None}
            rows.append(row);print(row)
    OUT.mkdir(parents=True,exist_ok=True)
    if rows:
        with (OUT/'model_benchmark.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        (OUT/'model_benchmark.json').write_text(json.dumps({'hardware':{'python':'3.13','cpu_threads':2,'gpu':'none'},'clips':[p.name for p in sorted(VIDEOS.glob('*.mp4'))],'labelled_accuracy_metrics':'NOT MEASURED: demo clips have no ground-truth annotations','runs':rows},indent=2))
        print('Wrote',OUT/'model_benchmark.csv')
if __name__=='__main__':main()
