#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fetch the PoultryGuard dataset corpus — spanning age (young chicks -> grown
broilers) and health (healthy vs sick / dead / injured, for red-box abnormality
ground truth) — from Roboflow Universe.

    pip install roboflow pyyaml
    python fetch_datasets.py --rf-key YOUR_ROBOFLOW_KEY

All sources are public and CC BY 4.0 (verify each project's page before
redistribution). Downloads land in  datasets_extra/<label>/  in YOLO format
(images + per-image .txt boxes + data.yaml with the class names).

Abnormality localisation convention used across the project:
    GREEN box = normal/healthy bird        RED box = abnormal (sick/dead/injured)
"""
from __future__ import annotations
import argparse, os, glob
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# label -> (roboflow_workspace, project, export_format, purpose)
SOURCES = {
    # --- age coverage ---
    "grown_broilers": ("gel", "broiler-chicken-hh3fw", "yolov11",
                       "Grown broilers, overhead house (counting) - the model's primary train set"),
    "young_chicks":   ("xogrox", "chicks-2oghi", "yolov11",
                       "Young / day-old chicks (small-bird coverage)"),
    # --- health / abnormality (red-box ground truth) ---
    "health_sick":    ("beproject-9ahd3", "chicken-detection-jmssr", "yolov11",
                       "Healthy vs sick chickens - classes Healtychicken / sickchicken"),
    "dead_injury":    ("inj", "pa5_7", "yolov11",
                       "Normal / dead / injured - classes chicken / chicken_dead / chicken_injury"),
}

ABNORMAL_KEYWORDS = ("sick", "dead", "injur", "abnormal", "unhealthy", "stress", "lethargic")


def is_abnormal(class_name: str) -> bool:
    n = class_name.lower()
    return any(k in n for k in ABNORMAL_KEYWORDS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rf-key", default=os.environ.get("RF_KEY", ""))
    ap.add_argument("--out", default=str(ROOT / "datasets_extra"))
    ap.add_argument("--only", nargs="*", default=list(SOURCES),
                    help="subset of labels to fetch (default: all)")
    args = ap.parse_args()
    if not args.rf_key:
        raise SystemExit("Pass --rf-key or set RF_KEY (free key from roboflow.com -> Settings -> API).")

    import yaml
    from roboflow import Roboflow
    rf = Roboflow(api_key=args.rf_key)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    print(f"{'label':16} {'classes':48} {'train/val/test'}")
    for label in args.only:
        ws, proj, fmt, _ = SOURCES[label]
        try:
            p = rf.workspace(ws).project(proj)
            v = int(str(p.versions()[0].version).split("/")[-1])
            ds = p.version(v).download(fmt, location=str(out / label))
            y = yaml.safe_load(open(Path(ds.location) / "data.yaml"))
            names = y.get("names", [])
            abn = [n for n in names if is_abnormal(n)]
            counts = [len(glob.glob(str(Path(ds.location) / s / "images" / "*")))
                      for s in ("train", "valid", "test")]
            tag = f"{names}" + (f"  (abnormal: {abn})" if abn else "")
            print(f"{label:16} {tag[:48]:48} {counts[0]}/{counts[1]}/{counts[2]}")
        except Exception as e:
            print(f"{label:16} FAILED: {type(e).__name__}: {e}")

    print("\nDone. Health datasets give the red-box abnormality ground truth; "
          "render with tools/render_ground_truth.py (green=healthy, red=abnormal).")


if __name__ == "__main__":
    main()
