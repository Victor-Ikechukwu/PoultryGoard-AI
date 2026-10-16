"""Central configuration for PoultryGuard.

All tunables live here so the Streamlit UI and the batch pipeline share one
source of truth.  Values are deliberately conservative defaults for a proof of
concept and are overridable from the sidebar at runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from pathlib import Path

# ---------------------------------------------------------------- paths
ROOT = Path(__file__).resolve().parent.parent          # .../PoultryGuard_PoC
DATA_DIR = ROOT / "data"
SAMPLES_DIR = DATA_DIR / "samples"
MODELS_DIR = ROOT / "models"
CASES_DIR = ROOT / "cases"                              # auto-saved evidence
DB_PATH = ROOT / "poultryguard.db"
DATASET_EXPORT_DIR = ROOT / "mortality_posture_dataset" # PDF: "Mortality Posture Dataset"

for _p in (DATA_DIR, SAMPLES_DIR, MODELS_DIR, CASES_DIR, DATASET_EXPORT_DIR):
    _p.mkdir(parents=True, exist_ok=True)

# Detector weights: a fine-tuned chicken model is preferred; we fall back to the
# generic YOLO11n (COCO 'bird') so the app always runs even before training.
CHICKEN_WEIGHTS = MODELS_DIR / "chicken.pt"
FALLBACK_WEIGHTS = ROOT.parent.parent / "Project BackUp" / "2024-25-2026-PHD" / \
    "Sindhu Maam" / "ImageProcessingRelated" / "paper1_DAZE" / "yolo11n.pt"


@dataclass
class Settings:
    # --- detection ---
    conf: float = 0.40          # higher conf suppresses litter false-positives
    iou: float = 0.50
    imgsz: int = 640            # match the detector's training resolution
    # Class names that should be treated as a live chicken. A fine-tuned model
    # typically emits 'chicken'/'broiler'; the generic COCO model emits 'bird'.
    chicken_classes: tuple = ("chicken", "broiler", "hen", "bird")
    dead_classes: tuple = ("dead", "dead_chicken", "mortality")
    use_slicing: bool = False     # SAHI-style tiled inference for very dense houses

    # --- tracking ---
    track_activation_threshold: float = 0.25
    minimum_matching_threshold: float = 0.8
    lost_track_buffer: int = 60

    # --- behaviour / mortality (seconds unless noted) ---
    fps_assumed: float = 15.0
    immobility_speed_px: float = 2.0      # centroid speed below this = "still"
    immobility_seconds: float = 8.0       # still for this long -> abnormal (demo scale)
    suspected_seconds: float = 20.0       # still this long + lying posture -> suspected mortality
    isolation_factor: float = 1.8         # neighbour distance > factor * median -> isolated
    premortality_window_s: float = 60.0   # PDF asks 30-60 min; compressed for demo

    # --- zone grid (localisation) ---
    zone_rows: int = 3        # A..C
    zone_cols: int = 4        # 1..4  -> A1..C4

    # --- flock context ---
    house_id: str = "House-1"
    farm_id: str = "Farm-A"
    flock_age_days: int = 18   # PDF monitors chicks age 0-45 days

    # --- environment early-warning target bands (broiler, age-dependent) ---
    # (low_ok, high_ok) used for the simulated early-warning system.
    temp_band_c: tuple = (28.0, 34.0)     # tightens with age in sensors.py
    humidity_band: tuple = (50.0, 70.0)   # %
    co2_band_ppm: tuple = (0.0, 3000.0)   # ppm, alarm above
    nh3_band_ppm: tuple = (0.0, 20.0)     # ppm, alarm above (25 ppm is a hard limit)

    def to_dict(self):
        return asdict(self)


DEFAULTS = Settings()

# Veterinary workflow enumerations -------------------------------------------
CASE_STATUS = ["open", "vet_notified", "under_review", "visit_booked",
               "examined", "follow_up", "closed"]

POSTURE_LABELS = [
    "standing_normal",
    "lying_right",
    "lying_left",
    "lying_back",
    "lying_chest",
    "body_curled",
    "neck_abnormal",
    "wing_open",
    "unknown",
]
