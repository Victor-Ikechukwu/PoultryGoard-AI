"""Export models/chicken.pt -> models/chicken.onnx.

Used by the GitHub Actions workflow (.github/workflows/export-onnx.yml) to keep
the deployed ONNX model in sync with the trained PyTorch weights, and runnable
locally the same way:

    python tools/export_onnx.py
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# chdir + relative path avoids ultralytics stripping apostrophes from the weight
# path on Windows (harmless on Linux CI).
os.chdir(ROOT)

SRC = Path("models/chicken.pt")
if not SRC.exists():
    print("models/chicken.pt not found — nothing to export.")
    sys.exit(0)

from ultralytics import YOLO

YOLO("models/chicken.pt").export(
    format="onnx", imgsz=640, opset=12, dynamic=False, simplify=False,
)
print("Exported models/chicken.onnx")
