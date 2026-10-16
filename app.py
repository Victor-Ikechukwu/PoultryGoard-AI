"""PoultryGuard - AI Smart Poultry Health Monitoring, Mortality Detection and
Veterinary Response System (Proof of Concept).

Features: bilingual UI (English / Arabic with RTL), light/dark themes, role-based
login (Admin / Veterinarian / Farm Operator), and a flicker-free live feed built
on Streamlit fragments.

Run:  streamlit run app.py
"""
from __future__ import annotations
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import streamlit as st

from poultryguard import config, vet, reporting, ui, i18n, auth
from poultryguard.database import DB
from poultryguard.pipeline import Pipeline
from poultryguard.sensors import EnvironmentSensors, target_temp_band

st.set_page_config(page_title="PoultryGuard AI", page_icon="🐔", layout="wide",
                   initial_sidebar_state="expanded")
DEMO_VIDEO = config.DATA_DIR / "demo_flock.mp4"


def ss(key, default):
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]

# --- language + theme (read widget state saved on the previous run) ---
ss("user", None)
lang = "ar" if st.session_state.get("lang_label") == i18n.LANGS["ar"] else "en"
theme = "dark" if st.session_state.get("dark_toggle") else "light"
ui.inject(theme, lang)
t = i18n.translator(lang)


# ============================================================= LOGIN SCREEN
def language_theme_controls(container):
    c1, c2 = container.columns([2, 1])
    c1.radio(t("language"), list(i18n.LANGS.values()), key="lang_label",
             horizontal=True, label_visibility="collapsed")
    c2.toggle("🌙 " + t("dark"), key="dark_toggle")


if st.session_state.user is None:
    st.markdown("<style>[data-testid='stSidebar']{display:none;}</style>", unsafe_allow_html=True)
    st.markdown('<div class="pg-login">', unsafe_allow_html=True)
    box = st.container()
    with box:
        language_theme_controls(st)
        st.markdown(f"""
<div class="pg-card">
  <div class="pg-login-brand"><div class="pg-badge">🐔</div>
    <div><div class="pg-title" style="color:var(--ink)">{t('app_title')}</div>
    <div class="pg-caption">{t('login_sub')}</div></div>
  </div>
""", unsafe_allow_html=True)
        st.markdown(f"#### {t('login_welcome')}")
        u = st.text_input(t("username"), placeholder="admin · vet · operator")
        p = st.text_input(t("password"), type="password", placeholder="admin123 · vet123 · farm123")
        if st.button(t("sign_in"), use_container_width=True, type="primary"):
            user = auth.authenticate(u, p)
            if user:
                st.session_state.user = user
                st.rerun()
            else:
                st.error(t("invalid_login"))
        hints = "<br>".join(f"• <b>{u}</b> / {pw} — {t(auth.ROLE_LABEL_KEY[r])}"
                            for u, pw, r in auth.DEMO_HINTS)
        st.markdown(f'<div class="pg-demo"><b>{t("demo_accounts")}</b><br>{hints}</div>',
                    unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


# ============================================================= AUTHENTICATED APP
user = st.session_state.user
role = user["role"]

@st.cache_resource(show_spinner="Loading detector + pipeline ...")
def get_pipeline():
    return Pipeline()

ss("running", False); ss("cap", None); ss("cap_sig", None)
ss("last_result", None); ss("counts_history", []); ss("sensor_hist", [])
db = DB()
pipe = get_pipeline()
sensors = ss("sensors", EnvironmentSensors(config.DEFAULTS))


# --------------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown(f"### 🐔 {t('app_title')}")
    st.caption(f"{t('signed_in_as')}: {user['name']} · {t(auth.ROLE_LABEL_KEY[role])}")
    language_theme_controls(st)
    if st.button("⇦ " + t("logout"), use_container_width=True):
        st.session_state.user = None
        st.session_state.running = False
        st.rerun()
    st.divider()

    with st.expander(t("farm_flock"), expanded=True):
        pipe.s.farm_id = st.text_input(t("farm_id"), pipe.s.farm_id)
        pipe.s.house_id = st.text_input(t("house_id"), pipe.s.house_id)
        pipe.s.flock_age_days = st.slider(t("flock_age"), 0, 45, pipe.s.flock_age_days)
        sensors.s = pipe.s

    with st.expander(t("detection"), expanded=False):
        pipe.s.conf = st.slider(t("confidence"), 0.05, 0.9, pipe.s.conf, 0.01)
        pipe.s.imgsz = st.select_slider(t("inf_size"), [416, 512, 640, 800, 960, 1280], pipe.s.imgsz)
        pipe.s.use_slicing = st.checkbox(t("tiled"), pipe.s.use_slicing)

    with st.expander(t("mortality_thresholds"), expanded=False):
        pipe.s.immobility_seconds = st.slider(t("immobile_abnormal"), 2.0, 30.0, pipe.s.immobility_seconds)
        pipe.s.suspected_seconds = st.slider(t("immobile_suspected"), 5.0, 120.0, pipe.s.suspected_seconds)
        pipe.s.zone_rows = st.number_input(t("zone_rows"), 1, 6, pipe.s.zone_rows)
        pipe.s.zone_cols = st.number_input(t("zone_cols"), 1, 8, pipe.s.zone_cols)
        pipe._zone = None

    st.divider()
    source = st.radio(t("camera_source"), [
        t("demo_video"), t("upload_video"), t("upload_images"), t("webcam"), t("ip_camera")])
    SRC = {t("demo_video"): "demo", t("upload_video"): "upvid", t("upload_images"): "upimg",
           t("webcam"): "webcam", t("ip_camera"): "rtsp"}[source]
    rtsp_url = ""; up_video = up_images = None
    if SRC == "rtsp":
        rtsp_url = st.text_input(t("stream_url"), "rtsp://user:pass@192.168.1.50:554/stream1")
    elif SRC == "upvid":
        up_video = st.file_uploader(t("upload_video"), ["mp4", "avi", "mov", "mkv"])
    elif SRC == "upimg":
        up_images = st.file_uploader(t("upload_images"), ["jpg", "jpeg", "png"], accept_multiple_files=True)
    st.caption(t("cam_note"))

    cc1, cc2 = st.columns(2)
    if cc1.button("▶ " + t("start"), use_container_width=True):
        st.session_state.running = True
    if cc2.button("■ " + t("stop"), use_container_width=True):
        st.session_state.running = False
    if st.button("🧪 " + t("inject_demo"), use_container_width=True, help=t("inject_help")):
        pipe.request_demo_event(); st.session_state.running = True

ui.header("fine-tuned chicken" if pipe.detector.is_finetuned else "generic fallback",
          pipe.s.farm_id, pipe.s.house_id, pipe.s.flock_age_days, t)


# --------------------------------------------------------------------- helpers
def _source_sig():
    return f"{SRC}|{rtsp_url}|{getattr(up_video,'name','') if up_video else ''}"

def open_capture():
    if SRC == "demo":
        return cv2.VideoCapture(str(DEMO_VIDEO)) if DEMO_VIDEO.exists() else None
    if SRC == "webcam":
        return cv2.VideoCapture(0)
    if SRC == "rtsp" and rtsp_url:
        return cv2.VideoCapture(rtsp_url)
    if SRC == "upvid" and up_video is not None:
        tmp = config.DATA_DIR / "uploaded_video.mp4"
        tmp.write_bytes(up_video.read())
        return cv2.VideoCapture(str(tmp))
    return None

def get_frame():
    sig = _source_sig()
    cap = st.session_state.cap
    if cap is None or not cap.isOpened() or st.session_state.cap_sig != sig:
        if cap is not None:
            cap.release()
        cap = open_capture()
        st.session_state.cap = cap; st.session_state.cap_sig = sig
    if cap is None:
        return None
    ok, frame = cap.read()
    if not ok:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0); ok, frame = cap.read()
    return frame if ok else None


# --------------------------------------------------------------------- tab renderers
def render_live():
    st.subheader(t("live_title"))
    st.markdown(f'<p class="pg-caption">{t("live_caption")}</p>', unsafe_allow_html=True)
    if SRC == "upimg" and up_images:
        st.session_state.running = False
        for f in up_images:
            arr = cv2.imdecode(np.frombuffer(f.read(), np.uint8), cv2.IMREAD_COLOR)
            pipe.reset_tracks()
            res = pipe.process_frame(arr, now=time.time())
            st.image(cv2.cvtColor(res.annotated, cv2.COLOR_BGR2RGB), use_container_width=True)
            st.caption(f"{f.name}: {t('counted')} **{res.count}** {t('chickens')}")
        return

    @st.fragment(run_every=0.08 if st.session_state.running else None)
    def live_view():
        if st.session_state.running:
            frame = get_frame()
            if frame is None:
                st.session_state.running = False
                st.warning(t("no_frame")); st.rerun(); return
            res = pipe.process_frame(frame, now=time.time())
            st.session_state.last_result = res
            st.session_state.counts_history.append(
                {"t": datetime.now().strftime("%H:%M:%S"), "count": res.count, "suspected": res.suspected})
            st.session_state.counts_history = st.session_state.counts_history[-240:]
            if res.new_case_ids:
                st.toast(f"🚨 {t('case_opened')}: #{res.new_case_ids[0]}", icon="🚨")
        res = st.session_state.last_result
        vcol, kcol = st.columns([3, 1], gap="medium")
        with vcol:
            if res is not None:
                st.image(cv2.cvtColor(res.annotated, cv2.COLOR_BGR2RGB), use_container_width=True)
            else:
                st.info(t("press_start"))
        with kcol:
            if res is not None:
                st.metric(t("live_count"), res.count,
                          f"{res.suspected} {t('suspected')}" if res.suspected else t("flock_stable"),
                          delta_color="inverse" if res.suspected else "off")
                st.metric(t("abnormal_resting"), res.abnormal)
                st.metric(t("pipeline_fps"), f"{res.fps:.1f}")
                rows = [{t("bird"): a.track_id, t("status"): a.state.value, "posture": a.posture,
                         t("zone"): a.zone, "s": round(a.immobile_s, 1), "score": a.score}
                        for a in res.assessments if a.state.value != "normal"]
                st.dataframe(pd.DataFrame(rows), height=220, use_container_width=True, hide_index=True)
    live_view()


def render_cases():
    st.subheader(t("cases_title"))
    cases = db.list_cases()
    if not cases:
        st.info(t("no_cases")); return
    dfc = pd.DataFrame(cases)[["id", "created_at", "chick_ref", "house_id", "zone",
                               "age_days", "detected_time", "posture", "score", "status"]]
    dfc["created_at"] = pd.to_datetime(dfc["created_at"], unit="s").dt.strftime("%Y-%m-%d %H:%M:%S")
    st.dataframe(dfc, use_container_width=True, height=230, hide_index=True)
    cid = st.selectbox(t("open_case"), [c["id"] for c in cases])
    case = db.get_case(cid)
    left, right = st.columns([1, 1], gap="large")
    with left:
        if case.get("snapshot_path") and Path(case["snapshot_path"]).exists():
            st.image(case["snapshot_path"], caption=f"{t('evidence')} — {t('bird')} {case['chick_ref']}, {t('zone')} {case['zone']}")
        if case.get("clip_path") and Path(case["clip_path"]).exists():
            st.video(case["clip_path"]); st.caption(t("evidence_clip"))
        st.markdown(ui.chip(f"{t('suspected_at')} · {t('zone')} {case['zone']} · {case['detected_time']}", "bad"),
                    unsafe_allow_html=True)
    with right:
        with st.container(border=True):
            st.markdown(reporting.build_case_report(case, db.actions_for(cid)))
    a, b, c = st.columns(3)
    if a.button("📧 " + t("notify_vet"), use_container_width=True):
        st.success(vet.notify_vet(db, cid)); st.rerun()
    slot = b.selectbox(t("visit_slot"), vet.next_slots(), label_visibility="collapsed")
    if c.button("📅 " + t("book_visit"), use_container_width=True):
        st.success(vet.book_visit(db, cid, slot)); st.rerun()


def render_vet():
    st.subheader(t("vet_title"))
    open_cases = [c for c in db.list_cases() if c["status"] != "closed"]
    if not open_cases:
        st.info(t("no_open_cases")); return
    cid = st.selectbox(t("case"), [c["id"] for c in open_cases], key="vet_case")
    case = db.get_case(cid)
    st.markdown(f"**{t('case')} #{cid}** · {case['house_id']} · {t('zone')} {case['zone']} · "
                f"{t('age')} {case['age_days']} · {t('status')} **{case['status']}**")
    # evidence: auto-captured snapshot + video clip
    if (case.get("snapshot_path") and Path(case["snapshot_path"]).exists()) or \
       (case.get("clip_path") and Path(case["clip_path"]).exists()):
        ev1, ev2 = st.columns(2)
        if case.get("snapshot_path") and Path(case["snapshot_path"]).exists():
            ev1.image(case["snapshot_path"], caption=t("evidence"))
        if case.get("clip_path") and Path(case["clip_path"]).exists():
            ev2.video(case["clip_path"]); ev2.caption(t("evidence_clip"))
    vet_name = st.text_input(t("veterinarian"), user["name"] if role == "vet" else "Dr. Vet")

    # Step 14 — veterinary case review, and Step 16 — on-site examination
    r1, r2 = st.columns([1, 2])
    if r1.button("🔍 " + t("review_case"), use_container_width=True):
        st.success(vet.review_case(db, cid, vet_name)); st.rerun()
    exam = r2.text_input(t("exam_findings"), label_visibility="collapsed", placeholder=t("exam_findings"))
    if r1.button("🩺 " + t("record_examination"), use_container_width=True) and exam:
        st.success(vet.record_examination(db, cid, exam, vet_name)); st.rerun()

    # Steps 17–18 — diagnosis / treatment / vaccination
    d1, d2, d3 = st.columns(3)
    diagnosis = d1.text_input(t("diagnosis"))
    treatment = d2.text_input(t("treatment"))
    vaccination = d3.text_input(t("vaccination"))
    b1, b2, b3 = st.columns(3)
    if b1.button(t("log_diagnosis"), use_container_width=True) and diagnosis:
        db.add_action(cid, "diagnosis", diagnosis, vet_name); db.update_case(cid, status="examined"); st.rerun()
    if b2.button(t("log_treatment"), use_container_width=True) and treatment:
        db.add_action(cid, "treatment", treatment, vet_name); st.rerun()
    if b3.button(t("log_vaccination"), use_container_width=True) and vaccination:
        db.add_action(cid, "vaccination", vaccination, vet_name); st.rerun()

    # Step 19 — follow-up monitoring, Step 20 — closure
    f1, f2, f3 = st.columns([1.2, 1.2, 1])
    fu_when = f1.text_input(t("follow_up_when"),
                            (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M"))
    fu_note = f2.text_input(t("follow_up_notes"))
    if f3.button("🔁 " + t("schedule_follow_up"), use_container_width=True):
        st.success(vet.schedule_follow_up(db, cid, fu_when, fu_note, vet_name)); st.rerun()
    if st.button("✅ " + t("close_case"), use_container_width=True):
        db.add_action(cid, "closed", "Case closed and database updated", vet_name)
        db.update_case(cid, status="closed"); st.rerun()
    acts = db.actions_for(cid)
    if acts:
        st.markdown(f"**{t('action_history')}**")
        dfa = pd.DataFrame(acts)[["created_at", "action", "detail", "vet_name"]]
        dfa["created_at"] = pd.to_datetime(dfa["created_at"], unit="s").dt.strftime("%H:%M:%S")
        st.dataframe(dfa, use_container_width=True, hide_index=True)


def render_env():
    st.subheader(t("env_title"))
    st.markdown(f'<p class="pg-caption">{t("env_caption")}</p>', unsafe_allow_html=True)
    ec = st.columns(5)
    if ec[0].button(t("spike_nh3"), use_container_width=True): sensors.trigger_anomaly("nh3", 20)
    if ec[1].button(t("spike_co2"), use_container_width=True): sensors.trigger_anomaly("co2", 3500)
    if ec[2].button(t("heat"), use_container_width=True): sensors.trigger_anomaly("temp", 6)
    if ec[3].button(t("cold"), use_container_width=True): sensors.trigger_anomaly("temp", -6)
    if ec[4].button(t("clear"), use_container_width=True): sensors.clear_anomalies()

    @st.fragment(run_every=1.5)
    def env_view():
        r = sensors.read(); alerts = sensors.evaluate(r); db.log_sensor(r, alerts)
        st.session_state.sensor_hist.append(
            {"t": datetime.now().strftime("%H:%M:%S"), "temp_c": r.temp_c,
             "humidity": r.humidity, "co2_ppm": r.co2_ppm, "nh3_ppm": r.nh3_ppm})
        st.session_state.sensor_hist = st.session_state.sensor_hist[-120:]
        tband = target_temp_band(pipe.s.flock_age_days)
        m = st.columns(4)
        m[0].metric(t("temp"), r.temp_c, f"{t('target')} {tband[0]}–{tband[1]}", delta_color="off")
        m[1].metric(t("humidity"), r.humidity, f"{t('target')} 50–70", delta_color="off")
        m[2].metric(t("co2"), int(r.co2_ppm), f"{t('limit')} 3000", delta_color="off")
        m[3].metric(t("nh3"), r.nh3_ppm, f"{t('limit')} 20", delta_color="off")
        if alerts:
            for a in alerts:
                (st.error if a.severity == "alarm" else st.warning)(f"{a.severity.upper()}: {a.message}")
        else:
            st.success(t("env_ok"))
        if st.session_state.sensor_hist:
            dh = pd.DataFrame(st.session_state.sensor_hist).set_index("t")
            g1, g2 = st.columns(2)
            g1.line_chart(dh[["temp_c", "humidity"]], height=220)
            g2.line_chart(dh[["co2_ppm", "nh3_ppm"]], height=220)
    env_view()


def render_dash():
    st.subheader(t("dash_title"))
    last = st.session_state.last_result
    k = st.columns(4)
    k[0].metric(t("current_count"), last.count if last else "—")
    k[1].metric(t("open_cases"), db.count_cases("open") + db.count_cases("vet_notified") + db.count_cases("visit_booked"))
    k[2].metric(t("total_cases"), db.count_cases())
    k[3].metric(t("flock_age_short"), f"{pipe.s.flock_age_days} d")
    if st.session_state.counts_history:
        st.markdown(f"**{t('count_suspected')}**")
        st.line_chart(pd.DataFrame(st.session_state.counts_history).set_index("t")[["count", "suspected"]], height=240)
    allc = db.list_cases()
    if allc:
        st.markdown(f"**{t('by_zone')}**")
        st.bar_chart(pd.DataFrame(allc).groupby("zone").size().rename("cases"), height=220)


def render_dataset():
    st.subheader(t("dataset_title"))
    st.markdown(f'<p class="pg-caption">{t("dataset_caption")}</p>', unsafe_allow_html=True)
    cases = db.list_cases()
    st.metric(t("captured"), len([c for c in cases if c.get("snapshot_path")]))
    if st.button("⬇ " + t("export")):
        import shutil
        out = config.DATASET_EXPORT_DIR; (out / "images").mkdir(parents=True, exist_ok=True)
        rows = []
        for c in cases:
            sp = c.get("snapshot_path")
            if sp and Path(sp).exists():
                shutil.copy2(sp, out / "images" / Path(sp).name)
                rows.append({"image": f"images/{Path(sp).name}", "posture": c["posture"],
                             "zone": c["zone"], "age_days": c["age_days"], "score": c["score"]})
        pd.DataFrame(rows).to_csv(out / "labels.csv", index=False)
        (out / "classes.txt").write_text("\n".join(config.POSTURE_LABELS))
        st.success(f"{t('export')}: {len(rows)} → {out}")


def render_req():
    st.subheader(t("req_title"))
    with st.container(border=True):
        st.markdown(f"**{t('pipeline')}** — full 20-step workflow")
        st.markdown("`Camera → Detection → Tracking → Behaviour → Abnormal → Suspected mortality "
                    "→ Posture → Location → Image/Video capture → DB registration → AI alert "
                    "→ Case report → Vet notification → Case review → Visit → Examination "
                    "→ Diagnosis → Treatment/Vaccination → Follow-up → Closure`")
    L, C, V, E, D = t("nav_live"), t("nav_cases"), t("nav_vet"), t("nav_env"), t("nav_dataset")
    cov = [
        ("1 · Camera feed (webcam / RTSP / upload)", "app.py sources", L),
        ("2 · Chick detection", "detector.py / detector_onnx.py", L),
        ("3 · Individual / group tracking", "pipeline.py (ByteTrack)", L),
        ("4 · Movement & behaviour analysis", "behavior.py", L),
        ("5 · Abnormal behaviour detection", "mortality.py (ABNORMAL)", L),
        ("6 · Suspected mortality detection", "mortality.py (SUSPECTED)", L),
        ("7 · Posture classification", "posture.py", C),
        ("8 · Location identification (zone)", "zones.py", C),
        ("9 · Automatic image/video capture", "pipeline._open_case (snapshot + clip)", C),
        ("10 · Case registration in database", "database.add_case", C),
        ("11 · AI health alert", "pipeline alert + live banner", L),
        ("12 · Automatic case report", "reporting.py (saved to disk)", C),
        ("13 · Veterinarian notification / call", "vet.notify_vet", C),
        ("14 · Veterinary case review", "vet.review_case", V),
        ("15 · Farm visit appointment", "vet.book_visit", C),
        ("16 · On-site veterinary examination", "vet.record_examination", V),
        ("17 · Diagnosis", "Vet Console", V),
        ("18 · Treatment / vaccination / medication", "Vet Console", V),
        ("19 · Follow-up monitoring", "vet.schedule_follow_up", V),
        ("20 · Case closure & database update", "Vet Console", V),
    ]
    st.dataframe(pd.DataFrame(cov, columns=[t("requirement"), t("implemented_in"), t("see_tab")]),
                 use_container_width=True, height=560, hide_index=True)
    st.markdown(f"### {t('detector')}")
    chick = config.CHICKEN_WEIGHTS; valp = config.ROOT / "results" / "VALIDATION.md"
    st.markdown(ui.chip(t("model_active") if chick.exists() else t("model_fallback"),
                        "ok" if chick.exists() else "warn"), unsafe_allow_html=True)
    if valp.exists():
        txt = valp.read_text(errors="ignore")
        def num(pat):
            m = re.search(pat, txt); return m.group(1) if m else "—"
        v = st.columns(4)
        v[0].metric(t("map50"), num(r"mAP@50:\s*\*\*([\d.]+)"))
        v[1].metric(t("precision"), num(r"Precision:\s*\*\*([\d.]+)"))
        v[2].metric(t("recall"), num(r"Recall:\s*\*\*([\d.]+)"))
        v[3].metric(t("count_err"), num(r"dense[^*]*\*\*([\d.]+%)"))
        st.caption(t("validated"))


# --------------------------------------------------------------------- role-based tabs
RENDER = {"live": render_live, "cases": render_cases, "vet": render_vet, "env": render_env,
          "dash": render_dash, "dataset": render_dataset, "req": render_req}
NAV = {"live": "nav_live", "cases": "nav_cases", "vet": "nav_vet", "env": "nav_env",
       "dash": "nav_dash", "dataset": "nav_dataset", "req": "nav_req"}

allowed = auth.allowed_tabs(role)
tab_objs = st.tabs([t(NAV[k]) for k in allowed])
for tab, key in zip(tab_objs, allowed):
    with tab:
        RENDER[key]()
