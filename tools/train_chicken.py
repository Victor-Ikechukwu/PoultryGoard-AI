"""Fine-tune a chicken detector for PoultryGuard.

Usage:
    python tools/train_chicken.py --data datasets/broiler-chicken-hh3fw/data_fixed.yaml \
        --epochs 30 --imgsz 512 --fraction 0.6 --device cpu

On completion the best weights are copied to models/chicken.pt, which the app
loads automatically in preference to the generic fallback.

Dataset: GEL "broiler-chicken" (Roboflow Universe, CC BY 4.0,
https://universe.roboflow.com/gel/broiler-chicken-hh3fw) -- single class 'chicken'.
"""
from __future__ import annotations
import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(ROOT / "datasets/broiler-chicken-hh3fw/data_fixed.yaml"))
    ap.add_argument("--weights", default=str(ROOT.parent.parent / "Project BackUp/2024-25-2026-PHD/Sindhu Maam/ImageProcessingRelated/paper1_DAZE/yolo11n.pt"))
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--imgsz", type=int, default=512)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--fraction", type=float, default=0.6)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--patience", type=int, default=12)
    args = ap.parse_args()

    from ultralytics import YOLO
    w = args.weights if Path(args.weights).exists() else "yolo11n.pt"
    model = YOLO(w)
    # NOTE: when the project path contains an apostrophe (e.g. Reem-Oman's-Project)
    # ultralytics' end-of-training auto-validation can crash while *reloading*
    # best.pt (it strips single quotes from the path). The weights are already
    # saved by then, so we guard the call and still publish best.pt -> chicken.pt.
    best = ROOT / "models" / "train" / "chicken" / "weights" / "best.pt"
    dest = ROOT / "models" / "chicken.pt"
    try:
        model.train(
            data=args.data, epochs=args.epochs, imgsz=args.imgsz, batch=args.batch,
            fraction=args.fraction, device=args.device, patience=args.patience,
            project=str(ROOT / "models" / "train"), name="chicken",
            exist_ok=True, verbose=True, plots=True,
        )
    except FileNotFoundError as e:
        print(f"[WARN] end-of-training step failed (likely apostrophe-path): {e}")
    finally:
        if best.exists():
            shutil.copy2(best, dest)
            print(f"\n[OK] copied best weights -> {dest}")
        else:
            print("[WARN] best.pt not found; training may have been interrupted")


if __name__ == "__main__":
    main()
