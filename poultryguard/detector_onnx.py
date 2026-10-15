"""Lightweight ONNX Runtime detector (no PyTorch / ultralytics).

Runs a YOLO model exported to ONNX using onnxruntime + numpy + OpenCV only, so
the cloud deployment can drop the ~1 GB torch+ultralytics stack. Exposes the
same surface as detector.Detector (detect(), names, is_finetuned,
weights_path) and returns the same Detection objects.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import cv2

from . import config
from .detector import Detection


def _letterbox(im, new=640, color=114):
    h, w = im.shape[:2]
    r = min(new / h, new / w)
    nh, nw = int(round(h * r)), int(round(w * r))
    resized = cv2.resize(im, (nw, nh), interpolation=cv2.INTER_LINEAR)
    top = (new - nh) // 2
    left = (new - nw) // 2
    out = np.full((new, new, 3), color, dtype=np.uint8)
    out[top:top + nh, left:left + nw] = resized
    return out, r, left, top


class OnnxDetector:
    def __init__(self, settings: config.Settings | None = None, weights: str | Path | None = None):
        import onnxruntime as ort
        self.s = settings or config.DEFAULTS
        self.weights_path = Path(weights or config.MODELS_DIR / "chicken.onnx")
        self.session = ort.InferenceSession(str(self.weights_path),
                                            providers=["CPUExecutionProvider"])
        self.inp = self.session.get_inputs()[0]
        self.out_name = self.session.get_outputs()[0].name
        # model input size (square); fall back to settings.imgsz
        shp = self.inp.shape
        self.imgsz = int(shp[2]) if isinstance(shp[2], int) and shp[2] > 0 else 640
        # class names from embedded metadata (ultralytics stores a dict string)
        meta = self.session.get_modelmeta().custom_metadata_map or {}
        self.names = {0: "chicken"}
        if "names" in meta:
            try:
                self.names = {int(k): v for k, v in json.loads(
                    meta["names"].replace("'", '"')).items()}
            except Exception:
                pass
        lname = {v.lower() for v in self.names.values()}
        self.is_finetuned = bool(lname & {"chicken", "broiler", "hen", "dead_chicken", "dead"})

    def detect(self, frame: np.ndarray) -> list[Detection]:
        img, r, dx, dy = _letterbox(frame, self.imgsz)
        blob = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        blob = np.transpose(blob, (2, 0, 1))[None]            # 1x3xHxW
        out = self.session.run([self.out_name], {self.inp.name: blob})[0]
        pred = np.squeeze(out, 0)                             # (4+nc, N)
        if pred.shape[0] < pred.shape[1]:
            pred = pred.T                                     # -> (N, 4+nc)
        boxes_xywh = pred[:, :4]
        scores_all = pred[:, 4:]
        cls_ids = scores_all.argmax(1)
        confs = scores_all.max(1)

        keep = confs >= self.s.conf
        boxes_xywh, confs, cls_ids = boxes_xywh[keep], confs[keep], cls_ids[keep]
        if len(boxes_xywh) == 0:
            return []

        # xywh (center, letterboxed space) -> xyxy in original image
        cx, cy, bw, bh = boxes_xywh.T
        x1 = (cx - bw / 2 - dx) / r
        y1 = (cy - bh / 2 - dy) / r
        x2 = (cx + bw / 2 - dx) / r
        y2 = (cy + bh / 2 - dy) / r

        nms_boxes = np.stack([x1, y1, x2 - x1, y2 - y1], 1).tolist()
        idxs = cv2.dnn.NMSBoxes(nms_boxes, confs.tolist(), self.s.conf, self.s.iou)
        if len(idxs) == 0:
            return []
        idxs = np.array(idxs).flatten()[:300]

        dead_set = {c.lower() for c in self.s.dead_classes}
        keep_names = {c.lower() for c in self.s.chicken_classes} | dead_set
        out_dets = []
        for i in idxs:
            label = str(self.names.get(int(cls_ids[i]), int(cls_ids[i]))).lower()
            if label not in keep_names:
                continue
            out_dets.append(Detection(
                xyxy=(float(x1[i]), float(y1[i]), float(x2[i]), float(y2[i])),
                conf=float(confs[i]), cls_name=label, is_dead=label in dead_set))
        return out_dets
