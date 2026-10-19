#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SAM-generated instance-segmentation masks with red/green health colouring.

For each ground-truth box in a YOLO health dataset, prompt Segment Anything
(MobileSAM via Ultralytics, CPU-friendly) to get a per-bird mask, then tint it:

    GREEN mask = healthy / normal bird      RED mask = abnormal (sick/dead/injured)

Usage:
    pip install ultralytics
    python sam_masks.py --dataset datasets_extra/health_sick --n 3 --only-abnormal
"""
from __future__ import annotations
import argparse, glob, os
from pathlib import Path
import numpy as np
import cv2
import yaml

ROOT = Path(__file__).resolve().parent.parent
GREEN = np.array([0, 200, 0], np.uint8)
RED = np.array([0, 0, 255], np.uint8)
ABNORMAL = ("sick", "dead", "injur", "abnormal", "unhealthy", "stress", "lethargic")


def is_abnormal(name: str) -> bool:
    n = name.lower()
    return any(k in n for k in ABNORMAL)


def gt_boxes(label_path: str, w: int, h: int):
    boxes, flags = [], []
    for line in open(label_path):
        p = line.split()
        if len(p) < 5:
            continue
        c = int(p[0]); cx, cy, bw, bh = map(float, p[1:5])
        x1, y1 = (cx - bw / 2) * w, (cy - bh / 2) * h
        x2, y2 = (cx + bw / 2) * w, (cy + bh / 2) * h
        boxes.append([x1, y1, x2, y2]); flags.append(c)
    return boxes, flags


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--out", default=str(ROOT / "results" / "gt_segmented"))
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--weights", default="mobile_sam.pt", help="mobile_sam.pt | sam_b.pt | sam2_b.pt")
    ap.add_argument("--only-abnormal", action="store_true")
    ap.add_argument("--alpha", type=float, default=0.45)
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

    from ultralytics import SAM
    sam = SAM(args.weights)

    for i, lp in enumerate(picks[:args.n]):
        img_path = next((lp.replace("labels", "images").replace(".txt", e)
                         for e in (".jpg", ".jpeg", ".png")
                         if os.path.exists(lp.replace("labels", "images").replace(".txt", e))), None)
        if not img_path:
            continue
        img = cv2.imread(img_path); h, w = img.shape[:2]
        boxes, cls = gt_boxes(lp, w, h)
        if not boxes:
            continue
        res = sam(img_path, bboxes=boxes, verbose=False, device="cpu")[0]
        if res.masks is None:
            print("no masks for", os.path.basename(img_path)); continue
        masks = res.masks.data.cpu().numpy().astype(bool)   # [N,H,W]

        colored = np.zeros_like(img)
        for j in range(min(len(masks), len(cls))):
            m = masks[j]
            if m.shape != (h, w):
                m = cv2.resize(m.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST).astype(bool)
            col = RED if is_abnormal(names[cls[j]]) else GREEN
            colored[m] = col
            cnts, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(img, cnts, -1, [int(x) for x in col], 2)
        any_mask = colored.any(axis=2)
        img[any_mask] = (img[any_mask] * (1 - args.alpha) + colored[any_mask] * args.alpha).astype(np.uint8)
        # labels
        for j in range(min(len(masks), len(cls))):
            x1, y1 = int(boxes[j][0]), int(boxes[j][1])
            col = RED if is_abnormal(names[cls[j]]) else GREEN
            cv2.putText(img, names[cls[j]], (x1, max(14, y1 - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, [int(x) for x in col], 2, cv2.LINE_AA)
        op = out / f"{root.name}_seg_{i+1}.jpg"
        cv2.imwrite(str(op), img)
        print("wrote", op, f"({len(masks)} masks)")


if __name__ == "__main__":
    main()
