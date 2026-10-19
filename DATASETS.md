# PoultryGuard — Dataset Corpus (age + health coverage)

Datasets covering the full brooding-to-finishing age range **and** health state,
with **red-box abnormality ground truth**. All are public Roboflow Universe
datasets (CC BY 4.0 — verify each project page before redistribution). Fetch
them all with:

```bash
pip install roboflow pyyaml
python tools/fetch_datasets.py --rf-key YOUR_ROBOFLOW_KEY
```

| Label | Source (Roboflow) | Classes | Train/Val/Test | Purpose |
|---|---|---|---|---|
| `grown_broilers` | `gel/broiler-chicken-hh3fw` | `chicken` | 1819 / 520 / 259 | **Grown broilers**, overhead house — the detector's main train set (mAP@50 0.954) |
| `young_chicks` | `xogrox/chicks-2oghi` | `chick` | 1520 / 179 / 0 | **Small / young chicks** (day-old–brooding) |
| `health_sick` | `beproject-9ahd3/chicken-detection-jmssr` | `Healtychicken`, `sickchicken` | 229 / 49 / 46 | **Healthy vs sick** ground truth — young chicks, mixed health |
| `dead_injury` | `inj/pa5_7` | `chicken`, `chicken_dead`, `chicken_injury` | 3 / 23 / 2 | **Dead / injured** ground truth |

## Age coverage
- **Small chickens / chicks:** `young_chicks` and `health_sick` (both are brooding-age chicks).
- **Grown-up broilers:** `grown_broilers` (overhead) + the 39-day field video
  (`data/testvids/broiler_39d.mp4`) used for the side-view test.

## Segmented ground truth & abnormality localisation
The health datasets carry **per-bird ground-truth boxes labelled by health state**.
`tools/render_ground_truth.py` draws them with the project convention:

> **GREEN = normal / healthy bird · RED = abnormal (sick / dead / injured)**

```bash
python tools/render_ground_truth.py --dataset datasets_extra/health_sick --only-abnormal --n 4
# -> results/gt_examples/health_sick_*.jpg  (sick chicks in red, healthy in green)
```

Example renders are in `results/gt_examples/`.

**Segmented ground truth (implemented):** `tools/sam_masks.py` turns the box
localisation into true **instance-segmentation masks** — it prompts **SAM**
(MobileSAM via Ultralytics, CPU-friendly) with each ground-truth box to get a
pixel-accurate per-bird mask, then tints it with the same health colouring
(RED = abnormal, GREEN = healthy):

```bash
pip install ultralytics
python tools/sam_masks.py --dataset datasets_extra/health_sick --n 3 --only-abnormal
# -> results/gt_segmented/health_sick_seg_*.jpg
```

Example renders are in `results/gt_segmented/`. Swap `--weights sam2_b.pt` for
SAM 2, or `sam_b.pt` for the full ViT-B SAM if you have a GPU.

## How this feeds the model
- Mixing `young_chicks` + `grown_broilers` into training gives **age-robust
  detection** (the current model, trained only on overhead broilers, under-detects
  the dense far field of a perspective/handheld view — see the 39-day video test).
- `health_sick` + `dead_injury` provide the labels to train the **posture/health
  classifier** that currently uses a geometry proxy — turning "suspected mortality"
  from a motion heuristic into a learned sick/dead/healthy prediction.
