"""Build the current, explicitly provisional faculty briefing deck."""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pathlib import Path

OUT=Path(__file__).with_name('faculty_briefing.pptx')
prs=Presentation();prs.slide_width= Inches(13.333);prs.slide_height= Inches(7.5)
BG=RGBColor(9,16,23); PANEL=RGBColor(17,28,38); TEAL=RGBColor(69,219,186); TEXT=RGBColor(235,243,247); MUTED=RGBColor(143,161,173); AMBER=RGBColor(255,179,77); RED=RGBColor(255,99,116); BLUE=RGBColor(121,169,255)

def base(title,sub=None,kicker='GOD\'S EYE · CAPSTONE PROTOTYPE'):
 s=prs.slides.add_slide(prs.slide_layouts[6]);s.background.fill.solid();s.background.fill.fore_color.rgb=BG
 box=s.shapes.add_textbox(Inches(.65),Inches(.32),Inches(12),Inches(.25));p=box.text_frame.paragraphs[0];p.text=kicker;p.font.size=Pt(10);p.font.bold=True;p.font.color.rgb=TEAL
 box=s.shapes.add_textbox(Inches(.65),Inches(.72),Inches(12),Inches(.5));p=box.text_frame.paragraphs[0];p.text=title;p.font.size=Pt(25);p.font.bold=True;p.font.color.rgb=TEXT
 if sub:
  box=s.shapes.add_textbox(Inches(.68),Inches(1.28),Inches(12),Inches(.38));p=box.text_frame.paragraphs[0];p.text=sub;p.font.size=Pt(11);p.font.color.rgb=MUTED
 foot=s.shapes.add_textbox(Inches(.65),Inches(7.14),Inches(12),Inches(.2));p=foot.text_frame.paragraphs[0];p.text='Human verification required  ·  No face recognition  ·  No identity linkage  ·  No automatic external alerting';p.font.size=Pt(8);p.font.color.rgb=MUTED
 return s

def text(s,x,y,w,h,lines,size=16,color=TEXT,bold=False):
 sh=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=sh.text_frame;tf.word_wrap=True
 for i,line in enumerate(lines):
  p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.text=line;p.font.size=Pt(size);p.font.color.rgb=color;p.font.bold=bold if i==0 else False;p.space_after=Pt(11)
 return sh

def card(s,x,y,w,h,label,body,accent=TEAL,body_size=14):
 sh=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h));sh.fill.solid();sh.fill.fore_color.rgb=PANEL;sh.line.color.rgb=RGBColor(34,48,61)
 text(s,x+.22,y+.17,w-.4,.3,[label.upper()],10,accent,True);text(s,x+.22,y+.58,w-.4,h-.7,body,body_size,TEXT)

# 1 title
s=prs.slides.add_slide(prs.slide_layouts[6]);s.background.fill.solid();s.background.fill.fore_color.rgb=BG
# large accent rails
sh=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(.7),Inches(1.1),Inches(.08),Inches(4.8));sh.fill.solid();sh.fill.fore_color.rgb=TEAL;sh.line.fill.background()
text(s,1.1,1.35,10.9,1.0,["GOD'S EYE"],36,TEXT,True)
text(s,1.12,2.35,10.8,1.15,["AI-powered public-space video analytics\nwith human-verified event cues"],23,TEAL,True)
text(s,1.15,4.25,10.8,1.0,["VIT Faculty Capstone · Working Prototype Briefing · 24 November 2026"],13,MUTED)
text(s,1.15,5.5,11,.7,["Local-first · CPU ONNX Runtime · No facial recognition · No automatic emergency contact"],12,AMBER,True)

# 2
s=base('Problem, objectives & responsible boundary','Transform authorized video into limited, auditable observations—not automated decisions.')
card(s,.7,1.9,3.85,3.9,'Problem',['Many camera feeds are difficult to monitor continuously.','Single frames do not establish temporal events.','Edge resources and privacy constrain always-on analytics.'],TEAL,15)
card(s,4.75,1.9,3.85,3.9,'Prototype objectives',['Detect common COCO objects and track short-lived local IDs.','Summarise people, vehicles, crowd thresholds and motion cues.','Create reviewable events, evidence and historical metrics.'],BLUE,15)
card(s,8.8,1.9,3.85,3.9,'Explicit exclusions',['No faces, identity, biometrics or demographic inference.','No intent/dangerousness/criminality prediction.','No automatic police/emergency contact; operators decide.'],AMBER,15)

# 3 architecture
s=base('Architecture: camera-local pipelines, shared CPU inference','Per-camera async capture; one serialized model session fits the tested two-core machine.')
labels=[('AUTHORISED\nSOURCE',.7,2.25,1.8),('OPENCV\nCAPTURE',2.75,2.25,1.8),('ONNX YOLO\n+ NMS',4.8,2.25,1.8),('TEMPORAL\nTRACK CUES',6.85,2.25,1.8),('FASTAPI\n+ SQL',8.9,2.25,1.8),('NEXT.JS\nDASHBOARD',10.95,2.25,1.8)]
for label,x,y,w in labels:
 sh=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(1.05));sh.fill.solid();sh.fill.fore_color.rgb=PANEL;sh.line.color.rgb=TEAL
 tf=sh.text_frame;tf.vertical_anchor=MSO_ANCHOR.MIDDLE;p=tf.paragraphs[0];p.text=label;p.alignment=PP_ALIGN.CENTER;p.font.size=Pt(12);p.font.bold=True;p.font.color.rgb=TEXT
for x in [2.5,4.55,6.6,8.65,10.7]:
 sh=s.shapes.add_shape(MSO_SHAPE.CHEVRON,Inches(x),Inches(2.56),Inches(.22),Inches(.36));sh.fill.solid();sh.fill.fore_color.rgb=TEAL;sh.line.fill.background()
card(s,1.0,4.0,5.3,1.7,'Persistence & controls',['SQLite locally / PostgreSQL option · event evidence expires','Human verification: Pending → acknowledged / verified / dismissed'],TEAL,13)
card(s,7.0,4.0,5.3,1.7,'Resource envelope',['2 CPU cores · no GPU · dynamic 320–640 input','One ONNX session shared by camera workers'],BLUE,13)

# 4 functionality
s=base('Prototype modules and honest status','The integrated path is running; event semantics remain deliberately conservative.')
card(s,.7,1.85,3.85,2.0,'Vision',['YOLOv8n object boxes, confidence and temporary IoU IDs.','People/vehicle counts and live overlay.'],TEAL,13)
card(s,4.75,1.85,3.85,2.0,'Temporal cues',['Downward displacement + sustained horizontal box.','Stationary object duration; fast image-plane movement.'],AMBER,13)
card(s,8.8,1.85,3.85,2.0,'Workflow',['Three event levels; evidence JPEGs.','Acknowledgement and verification controls.'],BLUE,13)
card(s,.7,4.1,5.85,1.8,'Limitations',['Fall cue is a heuristic state machine, not a trained/validated action classifier.','Traffic/minute is a new-track proxy, not calibrated line crossing.'],RED,12)
card(s,6.8,4.1,5.85,1.8,'Outstanding evaluation',['No labelled target-domain results yet: no P/R/F1/mAP or event recall claims.','Pose model exported but not used in default CPU pipeline.'],AMBER,12)

# 5 measured results
s=base('Measured CPU trade-off (one 80-frame run per row)','Local inference benchmark: first 20 frames from each of four CC BY 4.0 sample clips.')
rows=[('FP32 320','13.71 ms','14.56 ms','68.62 fps'),('FP32 416','24.07 ms','28.76 ms','39.35 fps'),('FP32 640','54.10 ms','62.29 ms','17.42 fps'),('INT8 320','62.79 ms','68.88 ms','15.68 fps'),('INT8 416','109.10 ms','124.98 ms','9.04 fps'),('INT8 640','240.13 ms','282.06 ms','4.11 fps')]
t=s.shapes.add_table(len(rows)+1,4,Inches(.9),Inches(1.9),Inches(11.6),Inches(3.6)).table
for j,h in enumerate(['Variant','Mean inference','P95 inference','Runner FPS']):t.cell(0,j).text=h
for i,row in enumerate(rows,1):
 for j,v in enumerate(row):t.cell(i,j).text=v
for i in range(len(rows)+1):
 for j in range(4):
  cell=t.cell(i,j);cell.fill.solid();cell.fill.fore_color.rgb=PANEL if i else RGBColor(18,54,48)
  for p in cell.text_frame.paragraphs:p.font.size=Pt(12);p.font.color.rgb=TEXT;p.font.bold=(i==0)
text(s,1.0,5.85,11.5,.55,['Live two-camera smoke, 15 s: 33.55 aggregate FPS · 90.2% system CPU · 220.5 MB max API RSS.'],13,TEAL,True)
text(s,1.0,6.45,11.5,.35,['INT8 is 4.6× slower at 320 px on this CPU. No accuracy labels; throughput is not a quality measure.'],10,AMBER)

# 6
s=base('Research gap & proposed contribution (hypothesis)','Prior work reports benchmark anomaly/tracking scores; operational multi-camera alert delay and CPU budgets differ.')
card(s,.75,1.9,5.7,3.9,'Gaps to test',['Offline frame AUC vs event-level false alerts and time-to-review.','Changing CPU load vs per-camera freshness and delay.','Privacy/retention often evaluated separately from event quality.','Traffic detections vs calibrated crossing-based flow.'],BLUE,14)
card(s,6.8,1.9,5.7,3.9,'BCLTE: Budgeted Camera-Local Temporal Evidence',['Allocate a bounded inference budget across cameras.','Accumulate short camera-local motion/count/persistence evidence.','Adapt cadence on low-change feeds; expose event delay and uncertainty.','No cross-camera identity joins; transient event evidence.'],TEAL,14)
text(s,1.0,6.05,11.5,.6,['Status: temporal cues and shared-session scheduling exist; adaptive cadence and labelled ablation remain unimplemented. No novelty claim yet.'],12,AMBER,True)

# 7
s=base('Evaluation and data governance','A reproducible benchmark requires permission, annotations and camera-disjoint testing.')
card(s,.75,1.9,5.7,3.8,'Plan',['Check primary dataset licence and access terms first.','Scene/camera-disjoint splits; three repeats and confidence intervals.','Detector: mAP, precision/recall; tracker: IDF1/HOTA.','Events: event P/R/F1, false alarms/camera-hour, delay.','Hardware: FPS, source age, CPU/GPU and peak RAM.'],TEAL,14)
card(s,6.8,1.9,5.7,3.8,'Data status',['Four Intel CC BY 4.0 clips included for demo only.','CrowdHuman: research/education terms; not mirrored.','UCSD/Avenue/ShanghaiTech/UCF-Crime/VIRAT: access/terms to confirm.','No public-dataset accuracy metrics reported.'],AMBER,14)

# 8
s=base('Demonstration sequence & next work','Working live preview and reproducible project files accompany this deck.')
card(s,.75,1.9,5.7,3.8,'Live walkthrough',['Overview → two sample feeds, counts and FPS.','Live Monitoring → annotated image and temporary track IDs.','Incidents → operator verify / acknowledge / dismiss.','Analytics → stored camera samples and event distribution.','Settings → change size, thresholds, model and retention.'],TEAL,14)
card(s,6.8,1.9,5.7,3.8,'Next research steps',['Obtain permission and annotation for event datasets.','Implement and benchmark budgeted cadence.','Validate fall/abandoned-object cues on temporal labels.','Add auth/RBAC and deployment security before wider use.','Complete faculty report after experiments.'],BLUE,14)
text(s,.9,6.2,11.5,.45,['Demo script: docs/demo_script.md  ·  Literature: docs/research_review.md  ·  Measures: docs/evaluation.md'],11,MUTED)

prs.save(OUT);print(OUT)
