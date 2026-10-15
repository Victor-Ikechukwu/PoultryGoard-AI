# 🐔 PoultryGuard — AI Smart Poultry Health Monitoring (Proof of Concept)

End-to-end prototype of the **AI-Based Smart Poultry Health Monitoring, Mortality
Detection, and Veterinary Response System** described in the project brief.
It runs as a **Streamlit** app, uses a **freely available dataset**, a real
**YOLO** detector, and demonstrates how the system integrates with cameras via
**live video feeds** (demo loop, webcam, or RTSP/HTTP IP cameras).

> This is a PoC to prove feasibility and cover every requirement. Section
> **"From PoC to product"** at the bottom lists what hardens it for commercial
> deployment.

---

## 1. Quick start

```bash
cd PoultryGuard_PoC
pip install -r requirements.txt        # ultralytics, supervision, streamlit, opencv...
streamlit run app.py                   # or double-click run_app.bat on Windows
```

Then in the browser:
1. **Sign in** — choose a demo account (see below). Pick language (English/العربية)
   and light/dark with the toggles at the top of the login screen or sidebar.
2. Pick a **Camera source** in the sidebar — start with *Demo video (sample loop)*.
3. Click **▶ Start** — watch live detection, counting, tracking and the zone grid.
4. Click **🧪 Inject demo mortality** to fire the full mortality → case → vet flow.
5. Walk the tabs available to your role.

The app runs immediately on a generic fallback detector; it automatically
upgrades to the fine-tuned chicken model as soon as training finishes (see §4).

### Access, roles, languages & themes
- **Login & roles** (`poultryguard/auth.py`) — each role sees only its tabs:
  | Demo login | Role | Tabs |
  |---|---|---|
  | `admin` / `admin123` | Administrator | all 7 |
  | `vet` / `vet123` | Veterinarian | Live, Cases, Vet Console, Environment, Dashboard, Requirements |
  | `operator` / `farm123` | Farm Operator | Live, Environment, Dashboard |

  These are **demo credentials** for the PoC. In production replace `USERS` with a
  real identity store (hashed passwords / SSO) — the `authenticate()` /
  `allowed_tabs()` interface is unchanged.
- **Bilingual** (`poultryguard/i18n.py`) — full **English / Arabic** UI with
  right-to-left layout and Arabic (Cairo) typography in Arabic mode.
- **Themes** — a **light / dark** toggle (custom switch); the whole app re-themes
  via CSS variables.

---

## 2. How it maps to every requirement in the brief

| # | Requirement (brief) | Where it lives | Tab |
|---|---|---|---|
| 1 | Live chick counting (object detection) | `detector.py`, `pipeline.py` | Live Monitor |
| 2 | Mortality detection (multi-frame immobility + posture) | `behavior.py`, `mortality.py` | Live Monitor |
| 3 | Location identification (zone / coordinates) | `zones.py` | Mortality Cases |
| 4 | Automatic documentation (snapshot + DB registration) | `pipeline._open_case`, `database.py` | Mortality Cases |
| 5 | Body-shape / posture analysis | `posture.py` | Mortality Cases |
| 6 | Vet case file + remote notification & farm-visit booking | `reporting.py`, `vet.py` | Mortality Cases |
| 7 | Vet action logging (diagnosis / treatment / vaccination / closure) | `database.vet_actions` | Vet Console |
| + | Posture classification at mortality (body profile) | `posture.PostureResult.profile` | Mortality Cases |
| + | Pre-mortality behaviour look-back (30–60 min) | `behavior.premortality_timeline` | Mortality Cases |
| + | Environmental early-warning (temp / humidity / CO₂ / NH₃) | `sensors.py` | Environment |
| + | Build a "Mortality Posture Dataset" | Dataset Export tab | Dataset Export |

**Pipeline (exactly as specified in the brief):**

```
Camera → Chick Detection → Individual/Group Tracking → Movement & Behaviour
Analysis → Abnormal Behaviour / Immobility → Posture Classification → Suspected
Mortality → Location Identification → Automatic Documentation → Case Registration
→ AI Health Alert → Vet Notification → Farm-Visit Booking → Exam / Diagnosis /
Treatment / Vaccination → Follow-up → Case Closure & DB Update
```

---

## 3. Architecture

```
app.py                      Streamlit UI (7 tabs)
poultryguard/
  config.py                 settings, thresholds, zone grid, environment bands
  detector.py               YOLO wrapper (counting) + pluggable chicken weights
  posture.py                posture / body-condition classifier (geometry; model-pluggable)
  behavior.py               per-track motion history (speed, immobility, isolation)
  mortality.py              immobility + posture → mortality state machine
  zones.py                  frame → zone id ("Zone B") localisation
  sensors.py                environmental sensor sim + early-warning fusion
  database.py               SQLite (cases, vet actions, sensor log)
  reporting.py              automatic veterinary case report
  vet.py                    vet notification / visit booking (mock gateway)
  draw.py                   overlays (boxes, ids, counter, zone grid, alerts)
  pipeline.py               per-frame orchestrator (ties it all together)
tools/train_chicken.py      fine-tune the detector on the chicken dataset
data/                       sample images + generated demo_flock.mp4
models/                     weights (chicken.pt when trained; generic fallback otherwise)
cases/                      auto-saved evidence snapshots + vet outbox
```

### Camera / live-feed integration
`app.py` reads frames through OpenCV `VideoCapture`, so the same pipeline drives:
- **Demo video** (`data/demo_flock.mp4`, generated from the sample images),
- **Local webcam** (`VideoCapture(0)`),
- **IP cameras** via **RTSP/HTTP** URL (e.g. `rtsp://user:pass@192.168.1.50:554/stream1`) —
  this is the production path: point it at a barn camera and it streams live.

---

## 4. The detector & dataset (freely available)

- **Dataset:** GEL *Broiler Chicken* — Roboflow Universe, **CC BY 4.0**
  (<https://universe.roboflow.com/gel/broiler-chicken-hh3fw>), 1 class `chicken`,
  ~2,600 images of dense broiler houses (up to 322 birds/image).
- **Model:** YOLO11n fine-tuned on that dataset. A first epoch already reaches
  **mAP@50 ≈ 0.92**. Training runs on CPU here (~6 min/epoch); on your GTX 1060 /
  any CUDA GPU it is far faster.

Re-train or extend any time:
```bash
python tools/train_chicken.py --epochs 30 --imgsz 512 --device cpu
# → writes models/chicken.pt, which the app picks up automatically
```
Until `models/chicken.pt` exists, the app falls back to the generic YOLO11n so it
always runs; counts on dense houses are low on the fallback and jump once the
fine-tuned weights land.

---

## 5. Notes on the PoC scope (honest boundaries)

- **Posture** uses a transparent geometry proxy (box shape + motion) behind a
  `PostureClassifier.predict()` interface. Drop a CNN trained on the *Mortality
  Posture Dataset* into `models/posture.*` to replace it — nothing else changes.
- **Mortality** is real multi-frame immobility + posture logic. The *Inject demo
  mortality* button forces one bird to "suspected" so the case→vet workflow is
  demonstrable on any feed; the underlying detector still fires on genuinely
  motionless birds.
- **Environmental sensors** are simulated (realistic drift + injectable
  anomalies) behind an interface a real Modbus/MQTT feed replaces.
- **Vet notification/booking** writes to a local outbox (`cases/vet_outbox.jsonl`);
  swap `vet._send` for an email/SMS/WhatsApp gateway.

## 6. Deploy to Streamlit Community Cloud

The app is packaged to run on a free Streamlit Cloud instance (≈1 GB RAM, 1 CPU,
no GPU). The detector runs on **ONNX Runtime**, so the heavy PyTorch + ultralytics
stack (~1 GB) is **not installed on the cloud** — only `models/chicken.onnx` (10 MB).

**Files that make it deployable**
| File | Purpose |
|---|---|
| `requirements.txt` | Lightweight runtime: `streamlit`, `onnxruntime`, `supervision`, `opencv-python-headless`, `numpy`, `pandas`. No torch/ultralytics. |
| `requirements-dev.txt` | Full local/training stack (torch, ultralytics, onnx, roboflow). |
| `packages.txt` | apt libs (`libgl1`, `libglib2.0-0`) for OpenCV. |
| `.gitignore` | Keeps the repo small — excludes `datasets/`, `models/train/`, `runs/`, `*.db`, `cases/`. |
| `models/chicken.onnx` | The detector the cloud app loads (commit this). |
| `.github/workflows/export-onnx.yml` | CI that re-exports `chicken.onnx` whenever `chicken.pt` changes. |

**Steps**
1. Push the repo to GitHub **including** `models/chicken.onnx` (and `data/demo_flock.mp4`,
   `data/samples/`). The `.gitignore` already drops the large folders.
2. On <https://share.streamlit.io> → *New app* → pick the repo, branch, and `app.py`.
   **Set the Python version to 3.12** in *Advanced settings* (the ML wheels have no
   Python 3.14 build — the repo also pins it via `.python-version`).
3. Deploy. First build installs the light stack (~1–2 min) and the app comes up on
   the demo video.

> **If you see `ModuleNotFoundError: cv2`** in the Cloud logs, the build picked Python 3.13/3.14.
> Fix: *Manage app → Settings → Python version → 3.12 → Reboot* (and confirm `.python-version`
> is committed). opencv/onnxruntime ship wheels only up to Python 3.12–3.13.

**Backend selection** — `poultryguard/detector.py::build_detector()` reads
`POULTRYGUARD_BACKEND` (`auto` | `onnx` | `torch`). `auto` (default) uses ONNX when
`chicken.onnx` is present and ultralytics is absent (i.e. on the cloud), and the
full torch model locally. ONNX and torch give **identical counts** (verified).

**Keeping the deployed model current** — `.github/workflows/export-onnx.yml` runs
on every push that changes `models/chicken.pt` (and can be triggered manually from
the Actions tab). It re-runs `python tools/export_onnx.py` and commits the refreshed
`models/chicken.onnx` back to the repo, which triggers a fresh Streamlit Cloud deploy.
So the flow after retraining is simply: **commit the new `chicken.pt` → CI exports and
commits `chicken.onnx` → cloud redeploys**. (Commit `chicken.pt` for the trigger to
fire; the workflow needs no secrets — it uses the built-in `GITHUB_TOKEN`.)

**Cloud limitations to know**
- **Cameras:** the cloud server can't reach a local webcam or a farm RTSP stream —
  use *Demo video* or *Upload* there. Webcam/RTSP are for local / edge deployments.
- **Storage is ephemeral:** the SQLite DB and saved snapshots reset when the app
  reboots. Fine for a demo; a real deployment points `config.DB_PATH` at a managed DB.

## 7. From PoC to product
Edge inference box per house (Jetson), real RTSP cameras + sensor nodes, a
posture CNN trained on captured data, fleet/multi-house backend, mobile vet app,
and auth/roles. See the accompanying cost model for the commercial build-out.

---

*AI output is decision-support / early-warning. The attending veterinarian makes
the final diagnosis and treatment decision.*
