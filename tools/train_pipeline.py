#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PoultryGuard — end-to-end chicken-detector training pipeline (single file).

Does everything in one run:
  1. Download the GEL "broiler-chicken" dataset from Roboflow Universe
     (https://universe.roboflow.com/gel/broiler-chicken-hh3fw, CC BY 4.0,
      single class 'chicken', 2,598 images = 1,819 train / 520 val / 259 test).
  2. Write a data YAML with ABSOLUTE paths (Roboflow's relative paths mis-resolve
     under ultralytics).
  3. Fine-tune YOLO11n from COCO-pretrained weights.
  4. Copy the best weights to models/chicken.pt.
  5. Export to models/chicken.onnx (the lightweight model the app runs).
  6. Validate on the held-out test split and print mAP / precision / recall.

Requirements:
    pip install ultralytics roboflow onnx

Run (first time, with a free Roboflow API key from roboflow.com -> Settings -> API):
    python train_pipeline.py --rf-key YOUR_ROBOFLOW_KEY

Re-train on an already-downloaded dataset:
    python train_pipeline.py --skip-download

Notes:
  * Defaults reproduce the shipped model: 30 epochs, 512 px, batch 16,
    fraction 0.6, AdamW (auto LR), CPU. Pass --device 0 to use a CUDA GPU.
  * Training at 512 px but exporting/validating at 640 px (--imgsz-infer) gave
    the best recall on small birds (see the paper's ablation).
  * The script `chdir`s to its own folder and uses relative weight paths so it
    works even when the project lives under a path containing an apostrophe
    (e.g. Reem-Oman's-Project), which otherwise breaks ultralytics' weight loader.
"""
from __future__ import annotations
import argparse
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent     # project root (holds datasets/, models/)
DATA_DIRNAME = "datasets"
MODELS_DIR = ROOT / "models"


def download_dataset(api_key: str, workspace: str, project: str, version: int,
                     out_dir: Path) -> Path:
    """Download the Roboflow dataset in YOLOv11 format. Returns the dataset folder."""
    from roboflow import Roboflow
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    rf = Roboflow(api_key=api_key)
    proj = rf.workspace(workspace).project(project)
    ds = proj.version(version).download("yolov11", location=str(out_dir))
    print(f"[download] dataset -> {ds.location}")
    return Path(ds.location)


def write_fixed_yaml(dataset_dir: Path) -> Path:
    """Write data_fixed.yaml with absolute train/val/test image paths."""
    yaml_path = dataset_dir / "data_fixed.yaml"
    yaml_path.write_text(
        f"train: {dataset_dir.as_posix()}/train/images\n"
        f"val:   {dataset_dir.as_posix()}/valid/images\n"
        f"test:  {dataset_dir.as_posix()}/test/images\n"
        f"nc: 1\n"
        f"names: ['chicken']\n",
        encoding="utf-8",
    )
    print(f"[yaml] wrote {yaml_path}")
    return yaml_path


def train(data_yaml: Path, args) -> Path:
    """Fine-tune YOLO11n; return the path to best.pt."""
    from ultralytics import YOLO
    model = YOLO(args.weights)                     # COCO-pretrained backbone
    best = MODELS_DIR / "train" / "chicken" / "weights" / "best.pt"
    try:
        model.train(
            data=str(data_yaml),
            epochs=args.epochs, imgsz=args.imgsz, batch=args.batch,
            fraction=args.fraction, device=args.device, patience=args.patience,
            optimizer="auto", project=str(MODELS_DIR / "train"), name="chicken",
            exist_ok=True, verbose=True, plots=True,
        )
    except FileNotFoundError as e:
        # ultralytics strips apostrophes from the weight path on the end-of-training
        # reload; the weights are already saved, so continue.
        print(f"[train] end-of-training reload skipped: {e}")
    return best


def publish_and_export(best: Path, imgsz_infer: int) -> Path:
    """Copy best.pt -> models/chicken.pt and export models/chicken.onnx."""
    dest = MODELS_DIR / "chicken.pt"
    if best.exists():
        shutil.copy2(best, dest)
        print(f"[publish] {best} -> {dest}")
    else:
        raise FileNotFoundError("best.pt not found; training may have failed")

    # chdir + relative path avoids ultralytics stripping apostrophes from the path
    cwd = os.getcwd()
    os.chdir(ROOT)
    try:
        from ultralytics import YOLO
        YOLO("models/chicken.pt").export(
            format="onnx", imgsz=imgsz_infer, opset=12, dynamic=False, simplify=False)
    finally:
        os.chdir(cwd)
    onnx = MODELS_DIR / "chicken.onnx"
    print(f"[export] {onnx}")
    return onnx


def validate(data_yaml: Path, imgsz_infer: int):
    """Validate chicken.pt on the held-out test split and print metrics."""
    cwd = os.getcwd()
    os.chdir(ROOT)
    try:
        from ultralytics import YOLO
        m = YOLO("models/chicken.pt")
        r = m.val(data=str(data_yaml), split="test", imgsz=imgsz_infer, conf=0.25, verbose=False)
        print("\n===== TEST-SET METRICS =====")
        print(f"mAP@50      : {r.box.map50:.3f}")
        print(f"mAP@50-95   : {r.box.map:.3f}")
        print(f"precision   : {r.box.mp:.3f}")
        print(f"recall      : {r.box.mr:.3f}")
    finally:
        os.chdir(cwd)


def main():
    ap = argparse.ArgumentParser(description="PoultryGuard chicken-detector training pipeline")
    ap.add_argument("--rf-key", default=os.environ.get("RF_KEY", ""),
                    help="Roboflow API key (or set RF_KEY env var)")
    ap.add_argument("--workspace", default="gel")
    ap.add_argument("--project", default="broiler-chicken-hh3fw")
    ap.add_argument("--version", type=int, default=9)
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--imgsz", type=int, default=512, help="training resolution")
    ap.add_argument("--imgsz-infer", type=int, default=640, help="export/val resolution")
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--fraction", type=float, default=0.6, help="fraction of train split per epoch")
    ap.add_argument("--device", default="cpu", help="'cpu' or a CUDA index like '0'")
    ap.add_argument("--patience", type=int, default=12)
    ap.add_argument("--weights", default="yolo11n.pt", help="starting weights (auto-downloaded)")
    ap.add_argument("--skip-download", action="store_true")
    ap.add_argument("--skip-train", action="store_true")
    ap.add_argument("--skip-export", action="store_true")
    ap.add_argument("--skip-val", action="store_true")
    args = ap.parse_args()

    dataset_dir = ROOT / DATA_DIRNAME / args.project

    if not args.skip_download:
        if not args.rf_key:
            raise SystemExit("A Roboflow API key is required. Pass --rf-key or set RF_KEY, "
                             "or use --skip-download if the dataset is already present.")
        download_dataset(args.rf_key, args.workspace, args.project, args.version, dataset_dir)
    data_yaml = write_fixed_yaml(dataset_dir)

    best = MODELS_DIR / "train" / "chicken" / "weights" / "best.pt"
    if not args.skip_train:
        best = train(data_yaml, args)
    if not args.skip_export:
        publish_and_export(best, args.imgsz_infer)
    if not args.skip_val:
        validate(data_yaml, args.imgsz_infer)
    print("\n[done] pipeline complete.")


if __name__ == "__main__":
    main()
