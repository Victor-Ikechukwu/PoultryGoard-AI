"""Veterinary notification & farm-visit booking (mock integration).

Implements PDF requirement #6 (notify the vet remotely and book a farm visit
through the system).  For the proof of concept notifications are written to the
case log and an outbox file; swap `_send` for an email/SMS/WhatsApp gateway in
production.
"""
from __future__ import annotations
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

from . import config


OUTBOX = config.CASES_DIR / "vet_outbox.jsonl"


def _send(payload: dict):
    """Mock transport: append to an outbox file. Replace with real gateway."""
    with open(OUTBOX, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def notify_vet(db, case_id: int, vet_name: str = "On-call Vet",
               channel: str = "app") -> str:
    case = db.get_case(case_id)
    msg = (f"[PoultryGuard] Suspected mortality — Case #{case_id}, "
           f"{case.get('farm_id')}/{case.get('house_id')}, Zone {case.get('zone')}, "
           f"age {case.get('age_days')}d, detected {case.get('detected_time')}. "
           f"Please review the attached case file.")
    _send({"ts": time.time(), "type": "notification", "channel": channel,
           "case_id": case_id, "to": vet_name, "message": msg})
    db.add_action(case_id, "notified", detail=f"via {channel}: {msg}", vet_name=vet_name)
    db.update_case(case_id, status="vet_notified")
    return msg


def next_slots(n: int = 3, start_hours: int = 2):
    base = datetime.now() + timedelta(hours=start_hours)
    return [(base + timedelta(hours=4 * i)).strftime("%Y-%m-%d %H:%M") for i in range(n)]


def book_visit(db, case_id: int, slot: str, vet_name: str = "On-call Vet") -> str:
    _send({"ts": time.time(), "type": "booking", "case_id": case_id,
           "to": vet_name, "slot": slot})
    db.add_action(case_id, "booked", detail=f"Farm visit booked for {slot}", vet_name=vet_name)
    db.update_case(case_id, status="visit_booked")
    return f"Visit booked for {slot} with {vet_name}"
