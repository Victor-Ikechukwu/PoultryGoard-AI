"""Posture / body-condition classification.

Implements PDF requirement #5 and the "Posture Classification at Mortality"
module (lying right/left/back/chest, body curled, legs/wings/neck abnormal).

Design note
-----------
A production system trains a CNN on the "Mortality Posture Dataset" (see the
PDF).  For the proof of concept we provide a *geometry-based* classifier that
reads posture from the detection box shape/orientation, behind the same
`PostureClassifier.predict()` interface.  Drop a trained Keras/torch model into
`models/posture.*` and swap the backend in one place -- the rest of the app is
untouched.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np

from . import config


@dataclass
class PostureResult:
    label: str
    confidence: float
    # Structured body profile mirroring the PDF case record fields.
    profile: dict = field(default_factory=dict)


class PostureClassifier:
    """Pluggable posture classifier.

    backend = 'geometry' (default, always available) or 'model' (loads a trained
    network if one is present in models/).
    """

    def __init__(self, settings: config.Settings | None = None, backend: str = "geometry"):
        self.s = settings or config.DEFAULTS
        self.backend = backend
        self._model = None
        if backend == "model":
            self._try_load_model()

    def _try_load_model(self):
        for ext in (".pt", ".onnx", ".keras", ".h5"):
            p = config.MODELS_DIR / f"posture{ext}"
            if p.exists():
                self._model_path = p
                # Hook: load torch/onnx/keras here. Left as a clear extension point.
                # self._model = load(...)
                break

    # ----------------------------------------------------------------- predict
    def predict(self, frame: np.ndarray, box, moving: bool) -> PostureResult:
        if self._model is not None:
            return self._predict_model(frame, box)
        return self._predict_geometry(box, moving)

    def _predict_model(self, frame, box):  # pragma: no cover - extension point
        raise NotImplementedError("Trained posture model hook not wired in PoC")

    def _predict_geometry(self, box, moving: bool) -> PostureResult:
        """Infer coarse posture from bounding-box geometry + motion.

        A standing/active bird tends to a compact, taller box; a bird lying down
        (prostrate) tends to a wider, flatter box.  This is a transparent proxy
        the vet can override, not a medical claim.
        """
        x1, y1, x2, y2 = box
        w = max(1.0, x2 - x1)
        h = max(1.0, y2 - y1)
        ar = w / h                     # aspect ratio (wide => likely lying)
        elongation = max(w, h) / min(w, h)

        if moving and ar < 1.25:
            label, conf = "standing_normal", 0.80
        elif ar >= 1.6:
            # flat & wide -> prostrate; left/right guessed from which half is taller
            label, conf = ("lying_chest" if elongation > 2.2 else "lying_left"), 0.55
        elif ar >= 1.25:
            label, conf = "lying_right", 0.50
        elif not moving:
            label, conf = "body_curled", 0.45
        else:
            label, conf = "standing_normal", 0.60

        profile = {
            "head": "curled" if label == "body_curled" else "normal",
            "neck": "abnormal" if label in ("lying_back", "neck_abnormal") else "normal",
            "legs": "stretched" if label.startswith("lying") else "normal",
            "wings": "open" if elongation > 2.4 else "folded",
            "body": "prostrate" if label.startswith("lying") else "upright",
            "aspect_ratio": round(ar, 2),
        }
        return PostureResult(label=label, confidence=conf, profile=profile)
