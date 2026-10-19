#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Render ground-truth localisation examples from a YOLO-format dataset, colouring
ABNORMAL birds (sick / dead / injured) RED and normal/healthy birds GREEN -
the "localization in red bounding boxes where chickens are suspected to have
abnormalities" view.

    python render_ground_truth.py --dataset datasets_extra/health_sick --n 4
"""
from __future__ import annotations
import argparse, glob, os
from pathlib import Path
import cv2, yaml

ROOT = Path(__file__).resolve().parent.parent
GREEN, RED = (0, 200, 0), (0, 0, 255)
ABNORMAL = ("sick", "dead", "injur", "abnormal", "unhealthy", "stress", "lethargic")


def is_abnormal(name: str) -> bool:
    n = name.lower()
    return any(k in n for k in ABNORMAL)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, help="YOLO dataset folder (has data.yaml + train/valid/test)")
    ap.add_argument("--out", default=str(ROOT / "results" / "gt_examples"))
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--only-abnormal", action="store_true",
                    help="only render frames that contain at least one abnormal bird")
    args = ap.parse_args()

    root = Path(args.dataset)
    names = yaml.safe_load(open(root / "data.yaml"))["names"]
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    picks = []
    for split in ("train", "valid", "test"):
        for lp in glob.glob(str(root / split / "labels" / "*.txt")):
            classes = [int(l.split()[0]) for l in open(lp) if l.split()]
            if not classes:
                continue
            if args.only_abnormal and not any(is_abnormal(names[c]) for c in classes):
                continue
            picks.append(lp)
        if len(picks) >= args.n:
            break

    for i, lp in enumerate(picks[:args.n]):
        img_path = None
        for ext in (".jpg", ".jpeg", ".png"):
            cand = lp.replace("labels", "images").replace(".txt", ext)
            if os.path.exists(cand):
                img_path = cand; break
        if not img_path:
            continue
        img = cv2.imread(img_path); h, w = img.shape[:2]
        for line in open(lp):
            p = line.split()
            if len(p) < 5:
                continue
            c = int(p[0]); cx, cy, bw, bh = map(float, p[1:5])
            x1, y1 = int((cx - bw / 2) * w), int((cy - bh / 2) * h)
            x2, y2 = int((cx + bw / 2) * w), int((cy + bh / 2) * h)
            col = RED if is_abnormal(names[c]) else GREEN
            cv2.rectangle(img, (x1, y1), (x2, y2), col, 3)
            cv2.putText(img, names[c], (x1, max(14, y1 - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 2, cv2.LINE_AA)
        op = out / f"{root.name}_{i+1}.jpg"
        cv2.imwrite(str(op), img)
        print("wrote", op)


if __name__ == "__main__":
    main()
