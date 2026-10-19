"""Per-frame orchestrator.

Implements the end-to-end PDF pipeline for one frame:

    Camera -> Detection -> Tracking -> Movement/Behaviour -> Abnormal/Immobility
    -> Posture classification -> Suspected mortality -> Zone localisation
    -> Automatic documentation (snapshot + DB case) -> (vet workflow downstream)

Returns an annotated frame plus structured telemetry the Streamlit UI renders.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import time
import numpy as np

from . import config, draw, reporting
from .detector import Detector, Detection, build_detector
from .posture import PostureClassifier
from .behavior import BehaviorTracker, median_neighbour_spacing
from .mortality import MortalityEngine, MortState
from .zones import ZoneMap
from .database import DB


@dataclass
class FrameResult:
    annotated: np.ndarray
    count: int
    suspected: int
    abnormal: int
    assessments: list = field(default_factory=list)   # BirdAssessment
    new_case_ids: list = field(default_factory=list)
    fps: float = 0.0


class Pipeline:
    def __init__(self, settings: config.Settings | None = None,
                 db: DB | None = None, detector: Detector | None = None):
        self.s = settings or config.DEFAULTS
        self.db = db or DB()
        self.detector = detector or build_detector(self.s)
        self.posture = PostureClassifier(self.s)
        self.behavior = BehaviorTracker(self.s)
        self.mortality = MortalityEngine(self.s)
        self._zone = None
        # rolling buffer of recent frames (down-scaled) for automatic VIDEO capture
        self._clip_fps = max(5, int(self.s.fps_assumed))
        self._frame_buf = deque(maxlen=self._clip_fps * 4)   # ~4 s of footage
        import supervision as sv
        self._sv = sv
        self.tracker = sv.ByteTrack(
            track_activation_threshold=self.s.track_activation_threshold,
            minimum_matching_threshold=self.s.minimum_matching_threshold,
            lost_track_buffer=self.s.lost_track_buffer,
            frame_rate=int(self.s.fps_assumed),
        )

    def _ensure_zone(self, frame):
        if self._zone is None:
            h, w = frame.shape[:2]
            self._zone = ZoneMap(w, h, self.s)
        return self._zone

    def reset_tracks(self):
        self.tracker.reset()
        self.behavior.tracks.clear()
        self.mortality.reported.clear()
        self._demo_pending = False

    def request_demo_event(self):
        """Force the next frame to escalate one tracked bird to suspected
        mortality, so the case -> documentation -> vet workflow can be
        demonstrated on any live feed. The underlying immobility logic is
        unchanged and still fires on genuinely motionless birds."""
        self._demo_pending = True

    # ---------------------------------------------------------------- frame
    def process_frame(self, frame: np.ndarray, now: float | None = None) -> FrameResult:
        t0 = time.time()
        now = now if now is not None else t0
        zone = self._ensure_zone(frame)
        sv = self._sv

        # buffer a down-scaled copy for automatic video capture
        try:
            import cv2
            h0, w0 = frame.shape[:2]
            if w0 > 640:
                fb = cv2.resize(frame, (640, int(640 * h0 / w0)))
            else:
                fb = frame.copy()
            self._frame_buf.append(fb)
        except Exception:
            pass

        dets: list[Detection] = self.detector.detect(frame)

        # -> supervision Detections for tracking
        if dets:
            xyxy = np.array([d.xyxy for d in dets], dtype=float)
            conf = np.array([d.conf for d in dets], dtype=float)
            cls = np.array([1 if d.is_dead else 0 for d in dets], dtype=int)
        else:
            xyxy = np.zeros((0, 4)); conf = np.zeros((0,)); cls = np.zeros((0,), dtype=int)
        sd = sv.Detections(xyxy=xyxy, confidence=conf, class_id=cls)
        sd = self.tracker.update_with_detections(sd)

        tracked = []     # (track_id, centroid)
        meta = {}        # track_id -> (box, is_dead)
        for i in range(len(sd)):
            tid = int(sd.tracker_id[i]) if sd.tracker_id is not None else -1
            if tid < 0:
                continue
            x1, y1, x2, y2 = sd.xyxy[i]
            c = ((x1 + x2) / 2.0, (y1 + y2) / 2.0)
            tracked.append((tid, c))
            meta[tid] = ((x1, y1, x2, y2), bool(sd.class_id[i]) if sd.class_id is not None else False)

        centroids = [c for _, c in tracked]
        med = median_neighbour_spacing(centroids)
        self.behavior.update(tracked, now, med)

        annotated = frame.copy()
        draw.draw_zone_grid(annotated, zone)

        forced_tid = None
        if getattr(self, "_demo_pending", False) and tracked:
            forced_tid = tracked[0][0]
            self._demo_pending = False

        assessments = []
        new_cases = []
        suspected = abnormal = 0
        for tid, c in tracked:
            box, is_dead = meta[tid]
            st = self.behavior.tracks.get(tid)
            immobile_s = st.immobile_seconds(now) if st else 0.0
            moving = (st.still_since is None) if st else True
            iso = self.behavior.isolation_score(tid, tracked, med)
            pr = self.posture.predict(frame, box, moving)
            if tid == forced_tid:               # demo injection (clearly flagged)
                pr.label, pr.confidence = "lying_chest", 0.60
                pr.profile.update({"body": "prostrate", "legs": "stretched",
                                   "head": "curled", "wings": "open"})
                pr.profile["demo_injected"] = True
                immobile_s = self.s.suspected_seconds + 2.0
                moving = False
            z = zone.zone_of(c)
            a = self.mortality.assess(tid, immobile_s, pr.label, pr.confidence,
                                      iso, z, is_dead_class=is_dead)
            a.posture_conf = pr.confidence
            assessments.append((a, pr, box))

            if a.state == MortState.SUSPECTED or a.state == MortState.REPORTED:
                suspected += 1
            elif a.state == MortState.ABNORMAL:
                abnormal += 1

            draw.draw_bird(annotated, box, tid, a.state.value,
                           posture=pr.label if a.state != MortState.NORMAL else None,
                           score=a.score if a.state != MortState.NORMAL else None)

            # automatic documentation + case registration
            if self.mortality.should_open_case(a):
                cid = self._open_case(frame, a, pr, box, zone)
                new_cases.append(cid)

        count = len(tracked)
        draw.draw_counter(annotated, count, dead=suspected,
                          extra=f"{self.s.farm_id}/{self.s.house_id} age {self.s.flock_age_days}d")
        if suspected:
            draw.banner(annotated, f"SUSPECTED MORTALITY x{suspected} - case(s) opened, vet alert ready")

        dt = max(1e-3, time.time() - t0)
        return FrameResult(annotated=annotated, count=count, suspected=suspected,
                           abnormal=abnormal,
                           assessments=[a for (a, _, _) in assessments],
                           new_case_ids=new_cases, fps=1.0 / dt)

    # ---------------------------------------------------------------- case
    def _open_case(self, frame, a, pr, box, zone) -> int:
        ts = datetime.now()
        chick_ref = f"{a.track_id:03d}"
        snap_dir = config.CASES_DIR
        snap_path = snap_dir / f"case_{ts.strftime('%Y%m%d_%H%M%S')}_bird{chick_ref}.jpg"
        # crop with margin for the evidence image
        try:
            import cv2
            x1, y1, x2, y2 = [int(v) for v in box]
            pad = 30
            h, w = frame.shape[:2]
            crop = frame[max(0, y1 - pad):min(h, y2 + pad), max(0, x1 - pad):min(w, x2 + pad)]
            ann = crop.copy()
            cv2.rectangle(ann, (pad if x1 - pad > 0 else x1, pad if y1 - pad > 0 else y1),
                          (ann.shape[1] - pad, ann.shape[0] - pad), (0, 0, 255), 2)
            cv2.imwrite(str(snap_path), ann)
        except Exception:
            snap_path = ""

        # --- automatic VIDEO capture: short clip from the rolling buffer ---
        clip_path = ""
        try:
            import cv2
            if len(self._frame_buf) >= 3:
                cp = snap_dir / f"case_{ts.strftime('%Y%m%d_%H%M%S')}_bird{chick_ref}.mp4"
                hh, ww = self._frame_buf[-1].shape[:2]
                vw = cv2.VideoWriter(str(cp), cv2.VideoWriter_fourcc(*"mp4v"),
                                     float(self._clip_fps), (ww, hh))
                for f in list(self._frame_buf):
                    if f.shape[:2] == (hh, ww):
                        vw.write(f)
                vw.release()
                clip_path = str(cp)
        except Exception:
            clip_path = ""

        premortality = self.behavior.premortality_timeline(a.track_id, time.time())
        cid = self.db.add_case(
            chick_ref=chick_ref, farm_id=self.s.farm_id, house_id=self.s.house_id,
            zone=a.zone, status="open", age_days=self.s.flock_age_days,
            detected_time=ts.strftime("%H:%M:%S"), posture=pr.label,
            posture_profile=pr.profile, immobile_s=a.immobile_s, isolation=a.isolation,
            score=a.score, reason=a.reason, snapshot_path=str(snap_path),
            clip_path=clip_path, premortality=premortality,
        )
        # --- AI health alert + auto-generated case report saved to disk ---
        self.db.add_action(cid, "alert",
                           f"AI health alert: suspected mortality (score {a.score}) at Zone {a.zone}, "
                           f"{ts.strftime('%H:%M:%S')}", vet_name="PoultryGuard AI")
        try:
            report_md = reporting.build_case_report(self.db.get_case(cid), self.db.actions_for(cid))
            rp = snap_dir / f"case_{ts.strftime('%Y%m%d_%H%M%S')}_bird{chick_ref}_report.md"
            rp.write_text(report_md, encoding="utf-8")
            self.db.update_case(cid, report_path=str(rp))
        except Exception:
            pass
        return cid
