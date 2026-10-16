"""SQLite persistence.

Implements PDF requirements #4 (automatic documentation / case registration in a
database) and #7 (veterinary action logging), plus a sensor log for the
environmental early-warning history.
"""
from __future__ import annotations
import sqlite3
import json
import time
from pathlib import Path

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at REAL,
    chick_ref TEXT,          -- e.g. bird track id formatted as 025
    farm_id TEXT,
    house_id TEXT,
    zone TEXT,
    status TEXT,             -- open | vet_notified | visit_booked | examined | closed
    age_days INTEGER,
    detected_time TEXT,      -- HH:MM:SS
    posture TEXT,
    posture_profile TEXT,    -- json
    immobile_s REAL,
    isolation REAL,
    score REAL,
    reason TEXT,
    snapshot_path TEXT,
    clip_path TEXT,          -- short video clip captured around the event
    report_path TEXT,        -- auto-generated case report saved to disk
    premortality TEXT        -- json timeline
);
CREATE TABLE IF NOT EXISTS vet_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER,
    created_at REAL,
    action TEXT,             -- notified | booked | diagnosis | treatment | vaccination | closed
    detail TEXT,
    vet_name TEXT,
    FOREIGN KEY(case_id) REFERENCES cases(id)
);
CREATE TABLE IF NOT EXISTS sensor_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    t REAL, temp_c REAL, humidity REAL, co2_ppm REAL, nh3_ppm REAL, alerts TEXT
);
"""


class DB:
    def __init__(self, path: str | Path | None = None):
        self.path = str(path or config.DB_PATH)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self._migrate()
        self.conn.commit()

    def _migrate(self):
        """Add columns to an existing DB created by an older schema."""
        have = {r[1] for r in self.conn.execute("PRAGMA table_info(cases)")}
        for col in ("clip_path", "report_path"):
            if col not in have:
                self.conn.execute(f"ALTER TABLE cases ADD COLUMN {col} TEXT")

    # ---- cases ----
    def add_case(self, **kw) -> int:
        kw.setdefault("created_at", time.time())
        kw.setdefault("status", "open")
        for jk in ("posture_profile", "premortality"):
            if isinstance(kw.get(jk), (dict, list)):
                kw[jk] = json.dumps(kw[jk])
        cols = ",".join(kw.keys())
        qs = ",".join("?" * len(kw))
        cur = self.conn.execute(f"INSERT INTO cases ({cols}) VALUES ({qs})", list(kw.values()))
        self.conn.commit()
        return cur.lastrowid

    def update_case(self, case_id: int, **kw):
        sets = ",".join(f"{k}=?" for k in kw)
        self.conn.execute(f"UPDATE cases SET {sets} WHERE id=?", [*kw.values(), case_id])
        self.conn.commit()

    def get_case(self, case_id: int):
        r = self.conn.execute("SELECT * FROM cases WHERE id=?", (case_id,)).fetchone()
        return dict(r) if r else None

    def list_cases(self, status: str | None = None):
        if status:
            rows = self.conn.execute("SELECT * FROM cases WHERE status=? ORDER BY id DESC", (status,)).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM cases ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]

    def count_cases(self, status: str | None = None) -> int:
        if status:
            return self.conn.execute("SELECT COUNT(*) FROM cases WHERE status=?", (status,)).fetchone()[0]
        return self.conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]

    # ---- vet actions ----
    def add_action(self, case_id: int, action: str, detail: str = "", vet_name: str = ""):
        self.conn.execute(
            "INSERT INTO vet_actions (case_id, created_at, action, detail, vet_name) VALUES (?,?,?,?,?)",
            (case_id, time.time(), action, detail, vet_name))
        self.conn.commit()

    def actions_for(self, case_id: int):
        rows = self.conn.execute("SELECT * FROM vet_actions WHERE case_id=? ORDER BY id", (case_id,)).fetchall()
        return [dict(r) for r in rows]

    # ---- sensors ----
    def log_sensor(self, r, alerts):
        self.conn.execute(
            "INSERT INTO sensor_log (t, temp_c, humidity, co2_ppm, nh3_ppm, alerts) VALUES (?,?,?,?,?,?)",
            (r.t, r.temp_c, r.humidity, r.co2_ppm, r.nh3_ppm, json.dumps([a.metric for a in alerts])))
        self.conn.commit()

    def recent_sensors(self, limit: int = 300):
        rows = self.conn.execute("SELECT * FROM sensor_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in reversed(rows)]
