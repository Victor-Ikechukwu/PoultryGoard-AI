"""Exercise the cloud runtime without the training stack or external services."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2
import numpy as np
import onnxruntime as ort
import supervision as sv
from streamlit.testing.v1 import AppTest
from poultryguard.config import Settings
from poultryguard.database import DB
from poultryguard.pipeline import Pipeline

print(f"Python {sys.version}")
print(f"OpenCV {cv2.__version__}, NumPy {np.__version__}, ONNX Runtime {ort.__version__}")
print(f"Supervision {sv.__version__}")
frame = np.zeros((640, 640, 3), dtype=np.uint8)
assert cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).shape == frame.shape
pipeline = Pipeline(settings=Settings(), db=DB(":memory:"))
assert pipeline.detector.__class__.__name__ == "OnnxDetector"
result = pipeline.process_frame(frame, now=0.0)
assert result.annotated.shape == frame.shape
assert result.count >= 0
pipeline.reset_tracks()
app = AppTest.from_file("app.py").run(timeout=60)
assert not app.exception, [x.message for x in app.exception]
assert len(app.text_input) == 2, "Expected the username and password fields"
assert "torch" not in sys.modules and "ultralytics" not in sys.modules
print("Cloud imports, ByteTrack, CPU ONNX inference and Streamlit login passed.")
