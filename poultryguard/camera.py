"""Robust camera capture for live feeds.

Wraps OpenCV VideoCapture with sensible behaviour for the three real sources a
deployment uses:

* ``webcam``  - a local USB/integrated camera by index (DirectShow on Windows,
  low-latency single-frame buffer).
* ``stream``  - an RTSP/HTTP IP camera (FFMPEG, TCP transport, 1-frame buffer,
  automatic throttled reconnect when the link drops).
* ``file``    - a recorded video (optionally looped for demos).

A failed read on a *live* source triggers a reconnect rather than a seek (the
old behaviour seeked to frame 0, which is meaningless for a stream).
"""
from __future__ import annotations
import os
import time
import platform
from pathlib import Path

import cv2

_IS_WINDOWS = platform.system() == "Windows"
_RECONNECT_THROTTLE_S = 2.0


class CameraSource:
    def __init__(self, kind: str, target=None, loop: bool = False,
                 width: int | None = None, height: int | None = None):
        self.kind = kind                 # 'webcam' | 'stream' | 'file'
        self.target = target
        self.loop = loop
        self.width = width
        self.height = height
        self.cap: cv2.VideoCapture | None = None
        self._opened_at = 0.0
        self._open()

    # ------------------------------------------------------------------ open
    def _open(self) -> bool:
        try:
            if self.kind == "webcam":
                idx = int(self.target or 0)
                self.cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW) if _IS_WINDOWS \
                    else cv2.VideoCapture(idx)
            elif self.kind == "stream":
                # low-latency RTSP over TCP
                os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp")
                self.cap = cv2.VideoCapture(str(self.target), cv2.CAP_FFMPEG)
            else:  # file
                self.cap = cv2.VideoCapture(str(self.target))
        except Exception:
            self.cap = None

        if self.cap is not None and self.kind in ("webcam", "stream"):
            self._try(cv2.CAP_PROP_BUFFERSIZE, 1)          # keep only the newest frame
            if self.width:
                self._try(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            if self.height:
                self._try(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._opened_at = time.time()
        return self.is_opened()

    def _try(self, prop, val):
        try:
            self.cap.set(prop, val)
        except Exception:
            pass

    # ------------------------------------------------------------------ api
    def is_opened(self) -> bool:
        return self.cap is not None and self.cap.isOpened()

    def read(self):
        """Return the next BGR frame, or None if unavailable this tick."""
        if self.cap is None:
            self._open()
            if self.cap is None:
                return None
        ok, frame = self.cap.read()
        if ok and frame is not None:
            return frame

        if self.kind == "file":
            if self.loop and self.cap is not None:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = self.cap.read()
                return frame if ok else None
            return None

        # live source dropped a frame -> throttled reconnect
        if time.time() - self._opened_at > _RECONNECT_THROTTLE_S:
            self.release()
            self._open()
        return None

    def release(self):
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
        self.cap = None


def make_source(kind: str, *, webcam_index: int = 0, stream_url: str = "",
                file_path: str | Path | None = None, loop: bool = False) -> CameraSource | None:
    """Factory used by the app. Returns None when the source is not configured."""
    if kind == "webcam":
        return CameraSource("webcam", webcam_index)
    if kind == "stream" and stream_url:
        return CameraSource("stream", stream_url)
    if kind == "file" and file_path and Path(file_path).exists():
        return CameraSource("file", file_path, loop=loop)
    return None
