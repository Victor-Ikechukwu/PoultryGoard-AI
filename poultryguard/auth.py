"""Role-based access for the PoultryGuard PoC.

Three roles with different tab access:
  - admin     : full access (all tabs + settings)
  - vet       : cases, vet console, dashboard, live view, environment, requirements
  - operator  : live monitor, environment, dashboard

Credentials here are DEMO accounts for the proof of concept (shown on the login
screen). In production, replace `USERS` with a real identity store (DB + hashed
passwords / SSO) — the `authenticate()` and `allowed_tabs()` interface stays the same.
"""
from __future__ import annotations
import hashlib

ALL_TABS = ["live", "cases", "vet", "env", "dash", "dataset", "req"]

ROLE_TABS = {
    "admin": ALL_TABS,
    "vet": ["live", "cases", "vet", "env", "dash", "req"],
    "operator": ["live", "env", "dash"],
}

ROLE_LABEL_KEY = {"admin": "role_admin", "vet": "role_vet", "operator": "role_operator"}


def _h(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


# DEMO accounts (proof of concept). password shown on the login screen.
USERS = {
    "admin":    {"name": "Administrator", "role": "admin",    "pw": _h("admin123")},
    "vet":      {"name": "Dr. Vet",       "role": "vet",      "pw": _h("vet123")},
    "operator": {"name": "Farm Operator", "role": "operator", "pw": _h("farm123")},
}

DEMO_HINTS = [
    ("admin", "admin123", "admin"),
    ("vet", "vet123", "vet"),
    ("operator", "farm123", "operator"),
]

# Accept the username OR a friendly alias (role name in English/Arabic) so users
# who type "Veterinarian" / "طبيب بيطري" instead of "vet" still get in.
ALIASES = {
    "admin": "admin", "administrator": "admin", "مدير النظام": "admin",
    "vet": "vet", "veterinarian": "vet", "vet doctor": "vet", "doctor": "vet",
    "طبيب بيطري": "vet", "طبيب": "vet",
    "operator": "operator", "farm operator": "operator", "مشغل المزرعة": "operator",
    "مشغّل المزرعة": "operator",
}


def _resolve(username: str) -> str:
    key = (username or "").strip().lower()
    return ALIASES.get(key, key)


def authenticate(username: str, password: str):
    uname = _resolve(username)
    u = USERS.get(uname)
    if u and u["pw"] == _h(password or ""):
        return {"username": uname, "name": u["name"], "role": u["role"]}
    return None


def allowed_tabs(role: str):
    return ROLE_TABS.get(role, ["live"])
