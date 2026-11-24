import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cv2
import numpy as np
from cv_engine import CameraState, Detection, IoUTracker, YoloDetector, iou


def test_iou_geometry():
    assert iou(np.array([0,0,10,10]),np.array([5,5,15,15])) == 25/175
    assert iou(np.array([0,0,2,2]),np.array([3,3,4,4])) == 0


def test_tracker_keeps_temporary_id():
    t=IoUTracker()
    a=Detection([0,0,20,50],0,'person',.9)
    b=Detection([1,1,21,51],0,'person',.8)
    t.update([a],1.0); t.update([b],1.1)
    assert a.track_id==b.track_id==1


def test_dynamic_detector_person_on_sample_video():
    model=Path(__file__).resolve().parents[1]/'models/yolov8n.onnx'
    video=Path(__file__).resolve().parents[2]/'data/media/person-bicycle-car-detection.mp4'
    cap=cv2.VideoCapture(str(video));cap.set(cv2.CAP_PROP_POS_FRAMES,30);ok,frame=cap.read();cap.release()
    assert ok
    det=YoloDetector(model,imgsz=416,confidence=.2)
    found,latency=det.infer(frame)
    assert latency>0
    assert any(d.label=='person' for d in found), [(d.label,d.confidence) for d in found]


def test_fall_cue_requires_temporal_sequence():
    state=CameraState('test');frame=np.zeros((200,200,3),dtype=np.uint8)
    sequence=[(0.0,[40,20,70,100]),(.1,[40,60,70,140]),(.2,[30,110,90,140])]
    sequence += [(.2+i*.2,[30,110,90,140]) for i in range(1,16)]
    observed=[]
    for t,box in sequence:
        _,events=state.analyze(frame,[Detection(box,0,'person',.9)],100+t,1.0)
        observed.extend(events)
    assert any(e['category']=='POSSIBLE_FALL' and e['severity']=='CRITICAL' for e in observed)
    assert 'Temporal cue' in next(e['description'] for e in observed if e['category']=='POSSIBLE_FALL')


def test_stationary_object_cue_is_duration_based():
    state=CameraState('test');frame=np.zeros((200,200,3),dtype=np.uint8);observed=[]
    base=time.time()
    for t in np.arange(0,16,.5):
        _,events=state.analyze(frame,[Detection([60,60,90,90],24,'backpack',.8)],base+float(t),1.0)
        observed.extend(events)
    assert any(e['category']=='STATIONARY_OBJECT' and e['severity']=='WARNING' for e in observed)


def test_vehicle_density_uses_clipped_union_of_observed_boxes():
    from cv_engine import bbox_union_area
    boxes=[Detection([-5,0,10,10],2,'car',.9),Detection([5,5,15,15],2,'car',.8)]
    assert bbox_union_area(boxes,20,20)==175


def test_traffic_flow_is_unknown_until_real_vehicle_track_history_exists():
    state=CameraState('traffic');frame=np.zeros((200,200,3),dtype=np.uint8)
    first,_=state.analyze(frame,[Detection([50,50,150,150],2,'car',.9)],10.0,1)
    assert first['traffic_density_level']=='VERY_HIGH'
    assert first['vehicle_box_occupancy_pct']==25.0
    assert first['traffic_flow'] is None
    stationary,_=state.analyze(frame,[Detection([50,50,150,150],2,'car',.9)],10.2,1)
    assert stationary['traffic_flow']=='STATIONARY'
    assert stationary['traffic_flow_tracks']==1


def test_traffic_flow_detects_motion_from_tracked_vehicle_centers():
    state=CameraState('traffic');frame=np.zeros((200,400,3),dtype=np.uint8)
    states=[]
    for t,x in [(20.0,40),(20.2,50),(20.4,60)]:
        metrics,_=state.analyze(frame,[Detection([x,70,x+45,95],2,'car',.9)],t,1)
        states.append(metrics['traffic_flow'])
    assert states[0] is None
    assert states[-1]=='MOVING'
