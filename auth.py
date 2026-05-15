"""
auth.py — Sistem autentikasi Agrinesia Dashboard
File-based storage (JSON) — tidak memerlukan MySQL untuk saat ini.
Mudah diganti ke MySQL nanti hanya dengan mengubah _load_users / _save_users.
"""
import json
import hashlib
from pathlib import Path

AUTH_FILE = Path(__file__).parent / "data" / "users.json"


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _default_users() -> dict:
    return {
        "admin": {
            "password": _hash("admin123"),
            "nama": "Administrator",
            "role": "admin",
        },
        "operator": {
            "password": _hash("operator123"),
            "nama": "Operator",
            "role": "operator",
        },
    }


def _load_users() -> dict:
    if AUTH_FILE.exists():
        with open(AUTH_FILE, "r") as f:
            return json.load(f)
    users = _default_users()
    _save_users(users)
    return users


def _save_users(users: dict) -> None:
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(AUTH_FILE, "w") as f:
        json.dump(users, f, indent=2)


# ── Public API ───────────────────────────────────────────────────────────────

def login(username: str, password: str) -> dict | None:
    """Return user dict jika berhasil, None jika gagal."""
    users = _load_users()
    user  = users.get(username.strip().lower())
    if user and user["password"] == _hash(password):
        return {"username": username.lower(), "nama": user["nama"], "role": user["role"]}
    return None


def get_all_users() -> list[dict]:
    """Daftar semua user tanpa password — untuk halaman manajemen user."""
    return [
        {"username": u, "nama": d["nama"], "role": d["role"]}
        for u, d in _load_users().items()
    ]


def add_user(username: str, password: str, nama: str, role: str) -> bool:
    """Tambah user baru. Return False jika username sudah ada."""
    users = _load_users()
    if username.lower() in users:
        return False
    users[username.lower()] = {"password": _hash(password), "nama": nama, "role": role}
    _save_users(users)
    return True


def change_password(username: str, old_pw: str, new_pw: str) -> bool:
    """Ganti password. Return False jika password lama salah."""
    users = _load_users()
    user  = users.get(username.lower())
    if not user or user["password"] != _hash(old_pw):
        return False
    users[username.lower()]["password"] = _hash(new_pw)
    _save_users(users)
    return True


def delete_user(username: str) -> bool:
    """Hapus user. Username 'admin' tidak bisa dihapus."""
    if username.lower() == "admin":
        return False
    users = _load_users()
    if username.lower() not in users:
        return False
    del users[username.lower()]
    _save_users(users)
    return True

