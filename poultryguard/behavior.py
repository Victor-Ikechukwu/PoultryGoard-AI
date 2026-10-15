"""Per-track behaviour & movement history.

Implements PDF requirement #1b (Individual/Group tracking, movement analysis)
and feeds the mortality engine and the pre-mortality (30-60 min look-back)
analysis.  Each tracked bird accumulates a short rolling history from which we
derive speed, immobility duration, and social isolation.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import deque
import math
import numpy as np

from . import config


@dataclass
class TrackState:
    track_id: int
    positions: deque = field(default_factory=lambda: deque(maxlen=2048))   # (t, cx, cy)
    speeds: deque = field(default_factory=lambda: deque(maxlen=2048))      # (t, px/s)
    last_zone: str = ""
    still_since: float | None = None      # timestamp motion dropped below threshold
    first_seen: float = 0.0
    last_seen: float = 0.0
    isolation: float = 0.0                 # 0..1, higher = more isolated

    def immobile_seconds(self, now: float) -> float:
        return 0.0 if self.still_since is None else max(0.0, now - self.still_since)

    def mean_speed(self, window_s: float, now: float) -> float:
        vals = [v for (t, v) in self.speeds if now - t <= window_s]
        return float(np.mean(vals)) if vals else 0.0


class BehaviorTracker:
    def __init__(self, settings: config.Settings | None = None):
        self.s = settings or config.DEFAULTS
        self.tracks: dict[int, TrackState] = {}

    def update(self, tracked, now: float, median_spacing: float):
        """tracked: list of (track_id, centroid). median_spacing: typical
        neighbour distance this frame, for isolation scoring."""
        seen = set()
        for tid, (cx, cy) in tracked:
            seen.add(tid)
            st = self.tracks.get(tid)
            if st is None:
                st = TrackState(track_id=tid, first_seen=now)
                self.tracks[tid] = st
            # instantaneous speed
            if st.positions:
                pt, px, py = st.positions[-1]
                dt = max(1e-3, now - pt)
                speed = math.hypot(cx - px, cy - py) / dt
            else:
                speed = 999.0  # unknown -> treat as moving on first sight
            st.positions.append((now, cx, cy))
            st.speeds.append((now, speed))
            st.last_seen = now

            # immobility state machine
            if speed < self.s.immobility_speed_px:
                if st.still_since is None:
                    st.still_since = now
            else:
                st.still_since = None

        # forget tracks not seen for a while
        stale = [tid for tid, st in self.tracks.items()
                 if now - st.last_seen > self.s.lost_track_buffer / self.s.fps_assumed]
        for tid in stale:
            self.tracks.pop(tid, None)

    def isolation_score(self, tid: int, tracked, median_spacing: float) -> float:
        """Distance to nearest neighbour relative to the flock median spacing."""
        me = dict(tracked).get(tid)
        if me is None or len(tracked) < 2 or median_spacing <= 0:
            return 0.0
        nn = min(math.hypot(me[0] - o[0], me[1] - o[1])
                 for t, o in tracked if t != tid)
        return float(min(1.0, (nn / median_spacing) / self.s.isolation_factor))

    def premortality_timeline(self, tid: int, now: float) -> list[dict]:
        """Down-sampled recent behaviour for the pre-mortality report
        (PDF: analyse 30-60 min before death: reduced movement, isolation,
        staying in one place, gait change)."""
        st = self.tracks.get(tid)
        if not st:
            return []
        out, last_t = [], None
        for (t, cx, cy), (_, v) in zip(st.positions, st.speeds):
            if now - t > self.s.premortality_window_s:
                continue
            if last_t is not None and t - last_t < 1.0:
                continue
            last_t = t
            out.append({"t_minus_s": round(now - t, 1),
                        "speed_px_s": round(v if v < 900 else 0.0, 1),
                        "x": round(cx, 1), "y": round(cy, 1)})
        return out


def median_neighbour_spacing(centroids) -> float:
    if len(centroids) < 2:
        return 0.0
    import numpy as np
    pts = np.array(centroids, dtype=float)
    nn = []
    for i in range(len(pts)):
        d = np.hypot(pts[:, 0] - pts[i, 0], pts[:, 1] - pts[i, 1])
        d[i] = np.inf
        nn.append(d.min())
    return float(np.median(nn))
