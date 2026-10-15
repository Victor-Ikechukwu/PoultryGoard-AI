"""Wait for fine-tuning to finish, then validate the chicken detector and render
clean proof images. Designed to be launched in the background right after
training starts; it blocks until models/chicken.pt appears (train_chicken.py
writes it on completion), then produces:

    results/VALIDATION.md          mAP + counting-error summary
    results/val_proof_*.jpg        annotated in-distribution frames

Run:  python tools/finalize_validation.py
"""
from __future__ import annotations
import sys, os, glob, time, cv2
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from poultryguard import config, draw
from poultryguard.detector import Detector
from poultryguard.zones import ZoneMap
from poultryguard.config import Settings

TEST = ROOT / "datasets" / "broiler-chicken-hh3fw"
DATA = TEST / "data_fixed.yaml"
BEST = config.MODELS_DIR / "train" / "chicken" / "weights" / "best.pt"
CHICK = config.CHICKEN_WEIGHTS


def gt_count(p):
    lp = TEST / "test" / "labels" / (Path(p).stem + ".txt")
    return sum(1 for _ in open(lp)) if lp.exists() else 0


def wait_for_model(timeout_h=5):
    deadline = time.time() + timeout_h * 3600
    while time.time() < deadline:
        if CHICK.exists():
            return str(CHICK)
        time.sleep(60)
    # fall back to the best checkpoint if the final copy never appeared
    return str(BEST) if BEST.exists() else None


def main():
    weights = wait_for_model()
    if not weights:
        print("[finalize] no weights found; aborting")
        return
    print(f"[finalize] validating {weights}")
    s = Settings()
    det = Detector(s, weights=weights)

    # 1) official detection metrics on the held-out test split
    lines = ["# PoultryGuard — Detector Validation", ""]
    try:
        m = det.model.val(data=str(DATA), split="test", imgsz=s.imgsz,
                          conf=0.25, verbose=False)
        lines += [
            f"- Weights: `{weights}`",
            f"- Test mAP@50: **{m.box.map50:.3f}**",
            f"- Test mAP@50-95: **{m.box.map:.3f}**",
            f"- Precision: **{m.box.mp:.3f}**   Recall: **{m.box.mr:.3f}**",
            "",
        ]
    except Exception as e:
        lines += [f"- (val metrics unavailable: {e})", ""]

    # 2) counting error on test images
    imgs = sorted(glob.glob(str(TEST / "test" / "images" / "*.jpg")))
    aerr = perr = n = 0
    dense = []
    for p in imgs:
        g = gt_count(p)
        pred = len(det.detect(cv2.imread(p)))
        aerr += abs(pred - g); n += 1
        if g >= 20:
            perr += abs(pred - g) / g
            dense.append((p, g, pred))
    lines += [
        f"- Mean absolute count error (all {n} test images): **{aerr / max(1, n):.1f}** birds",
        f"- Mean % count error (dense images, GT>=20): "
        f"**{100 * perr / max(1, len(dense)):.1f}%**  over {len(dense)} images",
        "",
    ]

    # 3) render clean proofs on the densest frames
    dense.sort(key=lambda t: t[1], reverse=True)
    for i, (p, g, pred) in enumerate(dense[:3]):
        img = cv2.imread(p)
        zm = ZoneMap(img.shape[1], img.shape[0], s)
        ann = img.copy(); draw.draw_zone_grid(ann, zm)
        for d in det.detect(img):
            x1, y1, x2, y2 = [int(v) for v in d.xyxy]
            cv2.rectangle(ann, (x1, y1), (x2, y2), (0, 200, 0), 2)
        draw.draw_counter(ann, len(det.detect(img)), extra=f"GT {g}")
        cv2.imwrite(str(config.ROOT / "results" / f"val_proof_{i+1}.jpg"), ann)

    (config.ROOT / "results" / "VALIDATION.md").write_text("\n".join(lines), encoding="utf-8")
    print("[finalize] DONE\n" + "\n".join(lines))


if __name__ == "__main__":
    main()
