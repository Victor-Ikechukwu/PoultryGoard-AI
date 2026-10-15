"""Frame annotation / overlays."""
from __future__ import annotations
import cv2

GREEN = (0, 200, 0)
AMBER = (0, 165, 255)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
GREY = (120, 120, 120)

STATE_COLOR = {
    "normal": GREEN,
    "abnormal": AMBER,
    "suspected": RED,
    "reported": RED,
}


def draw_zone_grid(frame, zonemap):
    xs, ys = zonemap.grid_lines()
    h, w = frame.shape[:2]
    for x in xs:
        cv2.line(frame, (x, 0), (x, h), GREY, 1)
    for y in ys:
        cv2.line(frame, (0, y), (w, y), GREY, 1)
    return frame


def draw_bird(frame, box, track_id, state, posture=None, score=None):
    x1, y1, x2, y2 = [int(v) for v in box]
    color = STATE_COLOR.get(state, GREEN)
    thick = 3 if state in ("suspected", "reported") else 1
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thick)
    if state in ("suspected", "reported", "abnormal"):
        label = f"#{track_id} {state}"
        if posture:
            label += f" {posture}"
        if score is not None:
            label += f" {score:.2f}"
        cv2.putText(frame, label, (x1, max(12, y1 - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2, cv2.LINE_AA)
    return frame


def draw_counter(frame, count, dead=0, extra=""):
    h, w = frame.shape[:2]
    bar_h = 42
    cv2.rectangle(frame, (0, 0), (w, bar_h), (20, 20, 20), -1)
    cv2.putText(frame, f"CHICKEN COUNTER  CURRENT: {count}", (10, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
    if dead:
        cv2.putText(frame, f"SUSPECTED: {dead}", (w - 230, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, RED, 2, cv2.LINE_AA)
    if extra:
        cv2.putText(frame, extra, (w - 430, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 1, cv2.LINE_AA)
    return frame


def banner(frame, text, color=RED):
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, h - 34), (w, h), color, -1)
    cv2.putText(frame, text, (10, h - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 2, cv2.LINE_AA)
    return frame
