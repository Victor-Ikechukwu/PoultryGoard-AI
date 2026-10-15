"""Mortality detection engine.

Implements PDF requirement #2 (suspected mortality detection) and the
"Mortality Detection and Posture Classification" module.  A bird is escalated
through a state machine based on how long it has been immobile, confirmed over
*several frames* (not a single image, per the PDF) and corroborated by a lying
posture.  A detector that directly emits a 'dead' class short-circuits to
suspected immediately.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

from . import config


class MortState(str, Enum):
    NORMAL = "normal"
    ABNORMAL = "abnormal"          # reduced movement / immobile
    SUSPECTED = "suspected"        # immobile long enough + lying posture
    REPORTED = "reported"          # a case has been opened for this bird


@dataclass
class BirdAssessment:
    track_id: int
    state: MortState = MortState.NORMAL
    immobile_s: float = 0.0
    posture: str = "unknown"
    posture_conf: float = 0.0
    isolation: float = 0.0
    zone: str = ""
    score: float = 0.0             # 0..1 mortality confidence
    reason: str = ""


class MortalityEngine:
    def __init__(self, settings: config.Settings | None = None):
        self.s = settings or config.DEFAULTS
        self.reported: set[int] = set()     # track_ids already turned into cases

    def assess(self, track_id: int, immobile_s: float, posture: str,
               posture_conf: float, isolation: float, zone: str,
               is_dead_class: bool = False) -> BirdAssessment:
        a = BirdAssessment(track_id=track_id, immobile_s=immobile_s,
                           posture=posture, posture_conf=posture_conf,
                           isolation=isolation, zone=zone)
        lying = posture.startswith("lying") or posture in ("body_curled", "neck_abnormal")

        # score = weighted blend of immobility, lying posture, isolation
        imm = min(1.0, immobile_s / max(1e-3, self.s.suspected_seconds))
        a.score = round(min(1.0, 0.6 * imm + 0.3 * (1.0 if lying else 0.0)
                            + 0.1 * isolation), 3)

        if is_dead_class:
            a.state, a.score, a.reason = MortState.SUSPECTED, 1.0, "detector flagged dead class"
        elif immobile_s >= self.s.suspected_seconds and lying:
            a.state = MortState.SUSPECTED
            a.reason = (f"immobile {immobile_s:.0f}s (>= {self.s.suspected_seconds:.0f}s) "
                        f"with posture '{posture}'")
        elif immobile_s >= self.s.immobility_seconds:
            a.state = MortState.ABNORMAL
            a.reason = f"reduced movement: immobile {immobile_s:.0f}s"
        else:
            a.state = MortState.NORMAL
            a.reason = "active"

        if track_id in self.reported and a.state == MortState.SUSPECTED:
            a.state = MortState.REPORTED
        return a

    def should_open_case(self, a: BirdAssessment) -> bool:
        if a.state == MortState.SUSPECTED and a.track_id not in self.reported:
            self.reported.add(a.track_id)
            return True
        return False
