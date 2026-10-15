"""Train a YOLOv8n baseline on the SAME broiler dataset for a fair SoTA
comparison against our YOLO11n. Writes metrics to results/compare_yolov8n.json.
Does NOT touch models/chicken.pt.
"""
from __future__ import annotations
import os, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
from ultralytics import YOLO

DATA = "datasets/broiler-chicken-hh3fw/data_fixed.yaml"
best = ROOT / "models" / "train" / "yolov8n" / "weights" / "best.pt"
try:
    YOLO("yolov8n.pt").train(data=DATA, epochs=30, imgsz=512, batch=16, fraction=0.6,
                             device="cpu", patience=12, project=str(ROOT/"models"/"train"),
                             name="yolov8n", exist_ok=True, verbose=True, plots=True)
except Exception as e:
    print("[warn] end step:", e)
# evaluate best on test split
if best.exists():
    m = YOLO(str(best))
    r = m.val(data=DATA, split="test", imgsz=640, conf=0.25, verbose=False)
    out = {"model": "YOLOv8n", "params_M": 3.0,
           "mAP50": round(float(r.box.map50), 4), "mAP50_95": round(float(r.box.map), 4),
           "precision": round(float(r.box.mp), 4), "recall": round(float(r.box.mr), 4)}
    (ROOT/"results"/"compare_yolov8n.json").write_text(json.dumps(out, indent=2))
    print("SAVED", out)
else:
    print("[warn] yolov8n best.pt not found")
