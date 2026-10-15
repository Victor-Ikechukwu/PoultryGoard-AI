"""Zone localisation.

Implements PDF requirement #3 (location identification inside the house, e.g.
"Suspected mortality - Zone B - 08:35").  Divides the frame into a rows x cols
grid and maps a pixel centroid to a human-readable zone label (A1 .. C4).
"""
from __future__ import annotations
import string
from . import config


class ZoneMap:
    def __init__(self, frame_w: int, frame_h: int, settings: config.Settings | None = None):
        s = settings or config.DEFAULTS
        self.rows = max(1, s.zone_rows)
        self.cols = max(1, s.zone_cols)
        self.w = frame_w
        self.h = frame_h

    def zone_of(self, centroid) -> str:
        cx, cy = centroid
        col = min(self.cols - 1, max(0, int(cx / max(1, self.w) * self.cols)))
        row = min(self.rows - 1, max(0, int(cy / max(1, self.h) * self.rows)))
        return f"{string.ascii_uppercase[row]}{col + 1}"

    def all_zones(self):
        return [f"{string.ascii_uppercase[r]}{c + 1}"
                for r in range(self.rows) for c in range(self.cols)]

    def grid_lines(self):
        """Pixel coordinates for drawing the grid overlay."""
        xs = [int(self.w * c / self.cols) for c in range(1, self.cols)]
        ys = [int(self.h * r / self.rows) for r in range(1, self.rows)]
        return xs, ys
