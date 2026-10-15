"""Chicken detector = YOLO wrapper.

Implements PDF requirement #1 (live chick counting via Object Detection).
Loads a fine-tuned chicken model when present, otherwise the generic YOLO11n so
the app is always runnable.  Optional SAHI-style tiled inference boosts recall
on very dense broiler houses.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import numpy as np

import os
import importlib.util

from . import config


@dataclass
class Detection:
    xyxy: tuple          # (x1, y1, x2, y2) in pixels
    conf: float
    cls_name: str
    is_dead: bool = False

    @property
    def centroid(self):
        x1, y1, x2, y2 = self.xyxy
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

    @property
    def wh(self):
        x1, y1, x2, y2 = self.xyxy
        return (x2 - x1, y2 - y1)


class Detector:
    def __init__(self, settings: config.Settings | None = None, weights: str | Path | None = None):
        from ultralytics import YOLO
        self.s = settings or config.DEFAULTS
        if weights is None:
            weights = config.CHICKEN_WEIGHTS if config.CHICKEN_WEIGHTS.exists() else config.FALLBACK_WEIGHTS
        self.weights_path = Path(weights)
        self.model = self._load_yolo(YOLO, self.weights_path)
        self.names = self.model.names
        # Is this a chicken-specialised model or the generic fallback?
        lname = {v.lower() for v in self.names.values()}
        self.is_finetuned = bool(lname & {"chicken", "broiler", "hen", "dead_chicken", "dead"})

    @staticmethod
    def _load_yolo(YOLO, weights_path: Path):
        """Load weights robustly even when the project path contains an
        apostrophe. Ultralytics strips single quotes from weight path strings
        (to tolerate pasted 'quoted/paths'), which corrupts any real path like
        .../Reem-Oman's-Project/...  We work around it by passing a path
        *relative to the project root* (which has no apostrophe) while the CWD
        is set to that root, so the string handed to YOLO never contains a quote.
        """
        import os
        wp = Path(weights_path)
        if "'" not in str(wp):
            return YOLO(str(wp))
        cwd0 = os.getcwd()
        try:
            os.chdir(config.ROOT)
            rel = os.path.relpath(wp, config.ROOT)
            if "'" in rel:                      # fall back to a symlink/copy-free temp hop
                import tempfile, shutil
                tmp = Path(tempfile.gettempdir()) / "poultryguard_weights"
                tmp.mkdir(exist_ok=True)
                dst = tmp / wp.name
                if not dst.exists() or dst.stat().st_mtime < wp.stat().st_mtime:
                    shutil.copy2(wp, dst)
                return YOLO(str(dst))
            return YOLO(rel)
        finally:
            os.chdir(cwd0)

    # -- helpers --------------------------------------------------------------
    def _label_of(self, cls_id: int) -> str:
        return str(self.names.get(int(cls_id), str(cls_id))).lower()

    def _keep(self, label: str) -> bool:
        return (label in {c.lower() for c in self.s.chicken_classes}
                or label in {c.lower() for c in self.s.dead_classes})

    # -- inference ------------------------------------------------------------
    def detect(self, frame: np.ndarray) -> list[Detection]:
        if self.s.use_slicing:
            return self._detect_sliced(frame)
        res = self.model.predict(frame, conf=self.s.conf, iou=self.s.iou,
                                 imgsz=self.s.imgsz, verbose=False)[0]
        return self._to_detections(res)

    def _to_detections(self, res) -> list[Detection]:
        out: list[Detection] = []
        if res.boxes is None:
            return out
        dead_set = {c.lower() for c in self.s.dead_classes}
        for b in res.boxes:
            label = self._label_of(b.cls)
            if not self._keep(label):
                continue
            xyxy = tuple(float(v) for v in b.xyxy[0].tolist())
            out.append(Detection(xyxy=xyxy, conf=float(b.conf[0]),
                                 cls_name=label, is_dead=label in dead_set))
        return out

    def _detect_sliced(self, frame: np.ndarray) -> list[Detection]:
        """Tiled inference for high-density scenes using supervision's slicer."""
        import supervision as sv

        def cb(tile: np.ndarray):
            r = self.model.predict(tile, conf=self.s.conf, iou=self.s.iou,
                                   imgsz=self.s.imgsz, verbose=False)[0]
            return sv.Detections.from_ultralytics(r)

        slicer = sv.InferenceSlicer(callback=cb, slice_wh=(640, 640),
                                    overlap_ratio_wh=(0.2, 0.2))
        dets = slicer(frame)
        out: list[Detection] = []
        dead_set = {c.lower() for c in self.s.dead_classes}
        for xyxy, _, conf, cls_id, _, _ in dets:
            label = self._label_of(cls_id)
            if not self._keep(label):
                continue
            out.append(Detection(xyxy=tuple(float(v) for v in xyxy), conf=float(conf),
                                 cls_name=label, is_dead=label in dead_set))
        return out


def _ultralytics_available() -> bool:
    return importlib.util.find_spec("ultralytics") is not None


def build_detector(settings: config.Settings | None = None, weights=None):
    """Return the best available detector backend.

    POULTRYGUARD_BACKEND = onnx | torch | auto (default).
    'auto' prefers the lightweight ONNX runtime when chicken.onnx exists and
    ultralytics/torch is not installed (e.g. on Streamlit Cloud), otherwise the
    full ultralytics detector.
    """
    settings = settings or config.DEFAULTS
    backend = os.environ.get("POULTRYGUARD_BACKEND", "auto").lower()
    onnx_path = config.MODELS_DIR / "chicken.onnx"
    use_onnx = (backend == "onnx") or (
        backend == "auto" and onnx_path.exists() and not _ultralytics_available())
    if use_onnx and onnx_path.exists():
        from .detector_onnx import OnnxDetector
        return OnnxDetector(settings, onnx_path)
    return Detector(settings, weights)
