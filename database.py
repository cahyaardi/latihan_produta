"""
database.py — MySQL backend untuk Produta
Semua kredensial dibaca dari .env / environment variable
"""

from __future__ import annotations
import os
import hashlib
import json
import re
import logging
from contextlib import contextmanager
from pathlib import Path

import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────────────────────
# LOAD ENV
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv(Path(__file__).parent / ".env")

logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host":     os.environ.get("MYSQL_HOST",     "localhost"),
    "port":     int(os.environ.get("MYSQL_PORT", "3306")),
    "user":     os.environ.get("MYSQL_USER",     "produta_user"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
    "database": os.environ.get("MYSQL_DATABASE", "produta_db"),
    "charset":  "utf8mb4",
    "connection_timeout": 10,
    "ssl_disabled": True,
}

_ADMIN_DEFAULT_PW = os.environ.get("ADMIN_DEFAULT_PASSWORD", "Admin@Produta2024!")

try:
    _pool = pooling.MySQLConnectionPool(
        pool_name="produta_pool",
        pool_size=10,
        **DB_CONFIG,
    )
except Exception as e:
    logger.error(f"Database connection failed: {e}")
    raise


# ─────────────────────────────────────────────────────────────────────────────
# CONNECTION
# ─────────────────────────────────────────────────────────────────────────────
@contextmanager
def get_conn():
    conn = _pool.get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"DB error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# PASSWORD UTILS
# ─────────────────────────────────────────────────────────────────────────────
def _hash(pw: str) -> str:
    """SHA-256 hash — password tidak pernah disimpan plaintext."""
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def _validate_password(pw: str) -> tuple[bool, str]:
    """Password policy: min 8 karakter, ada huruf besar, kecil, dan angka."""
    if len(pw) < 8:
        return False, "Password minimal 8 karakter."
    if not re.search(r"[A-Z]", pw):
        return False, "Password harus mengandung huruf kapital."
    if not re.search(r"[a-z]", pw):
        return False, "Password harus mengandung huruf kecil."
    if not re.search(r"\d", pw):
        return False, "Password harus mengandung angka."
    return True, ""

def _validate_username(uname: str) -> tuple[bool, str]:
    """Username: 3-30 karakter, hanya huruf/angka/underscore."""
    if not re.match(r"^[a-zA-Z0-9_]{3,30}$", uname):
        return False, "Username hanya boleh huruf, angka, underscore (3-30 karakter)."
    return True, ""


# ─────────────────────────────────────────────────────────────────────────────
# INIT SCHEMA
# ─────────────────────────────────────────────────────────────────────────────
def init_db():
    """Buat semua tabel dan seed data awal. Aman dijalankan berulang kali."""
    with get_conn() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id         INT AUTO_INCREMENT PRIMARY KEY,
                username   VARCHAR(30) UNIQUE NOT NULL,
                password   VARCHAR(255) NOT NULL,
                nama       VARCHAR(100) NOT NULL,
                role       ENUM('admin','operator') NOT NULL DEFAULT 'operator',
                is_active  TINYINT(1) NOT NULL DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                id         INT AUTO_INCREMENT PRIMARY KEY,
                username   VARCHAR(30) NOT NULL,
                ip_address VARCHAR(45),
                success    TINYINT(1) NOT NULL DEFAULT 0,
                attempt_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_username_time (username, attempt_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS defect_data (
                id           INT AUTO_INCREMENT PRIMARY KEY,
                jenis_defect VARCHAR(100) NOT NULL,
                frekuensi    INT NOT NULL DEFAULT 0,
                updated_by   VARCHAR(30),
                updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP
                             ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS demand_history (
                id         INT AUTO_INCREMENT PRIMARY KEY,
                tanggal    DATE NOT NULL,
                permintaan INT NOT NULL,
                produk     VARCHAR(100) NOT NULL DEFAULT 'LBS BLACK FOREST',
                added_by   VARCHAR(30),
                added_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_tanggal (tanggal),
                INDEX idx_produk (produk)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS suhu_data (
                id        INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME NOT NULL,
                zona1     FLOAT,
                zona2     FLOAT,
                zona3     FLOAT,
                zona4     FLOAT,
                added_by  VARCHAR(30),
                added_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uniq_ts (timestamp),
                INDEX idx_ts (timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS destinasi (
                id         INT AUTO_INCREMENT PRIMARY KEY,
                nama       VARCHAR(100) NOT NULL,
                demand     INT NOT NULL DEFAULT 0,
                latitude   DOUBLE NOT NULL,
                longitude  DOUBLE NOT NULL,
                aktif      TINYINT(1) NOT NULL DEFAULT 1,
                updated_by VARCHAR(30),
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                           ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS hasil_rute (
                id            INT AUTO_INCREMENT PRIMARY KEY,
                run_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
                run_by        VARCHAR(30),
                n_vehicles    INT,
                capacity      INT,
                total_dist_km DOUBLE,
                status_solver VARCHAR(50),
                routes_json   LONGTEXT,
                params_json   LONGTEXT,
                INDEX idx_run_at (run_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        # Seed admin
        cur.execute("SELECT COUNT(*) AS n FROM users")
        if cur.fetchone()["n"] == 0:
            cur.execute(
                "INSERT INTO users (username, password, nama, role) VALUES (%s,%s,%s,%s)",
                ("admin", _hash(_ADMIN_DEFAULT_PW), "Administrator", "admin")
            )
        # Seed defect data
        cur.execute("SELECT COUNT(*) AS n FROM defect_data")
        if cur.fetchone()["n"] == 0:
            cur.executemany(
                "INSERT INTO defect_data (jenis_defect, frekuensi) VALUES (%s,%s)",
                [("Tinggi kurang dari 4 cm",62),("Basah",45),("Belah",15),
                 ("Permukaan kue Kering",11),("Warna kurang sesuai",11),
                 ("Tekstur Crumbling",5),("Bantet",0)]
            )


# ─────────────────────────────────────────────────────────────────────────────
# AUTH — dengan brute force protection
# ─────────────────────────────────────────────────────────────────────────────
MAX_ATTEMPTS = 5          # maks gagal login
LOCKOUT_MINUTES = 15      # durasi lockout

def _log_attempt(username: str, success: bool):
    try:
        with get_conn() as cur:
            cur.execute(
                "INSERT INTO login_attempts (username, success) VALUES (%s, %s)",
                (username[:30], int(success))
            )
    except Exception:
        pass

def _is_locked(username: str) -> tuple[bool, int]:
    """Cek apakah user terkunci karena terlalu banyak gagal login."""
    with get_conn() as cur:
        cur.execute("""
            SELECT COUNT(*) AS n FROM login_attempts
            WHERE username=%s AND success=0
              AND attempt_at > NOW() - INTERVAL %s MINUTE
        """, (username[:30], LOCKOUT_MINUTES))
        n = cur.fetchone()["n"]
    if n >= MAX_ATTEMPTS:
        return True, LOCKOUT_MINUTES
    return False, 0

def login(username: str, password: str) -> dict | None:
    """Login dengan proteksi brute force. Return user dict atau None."""
    username = username.strip()[:30]
    locked, wait = _is_locked(username)
    if locked:
        raise PermissionError(f"Akun dikunci sementara. Coba lagi dalam {wait} menit.")
    with get_conn() as cur:
        cur.execute(
            "SELECT * FROM users WHERE username=%s AND is_active=1",
            (username,)
        )
        user = cur.fetchone()
    if user and user["password"] == _hash(password):
        _log_attempt(username, success=True)
        # Update last_login
        try:
            with get_conn() as cur:
                cur.execute(
                    "UPDATE users SET last_login=NOW() WHERE username=%s",
                    (username,)
                )
        except Exception:
            pass
        # Jangan kirim password hash ke app
        return {k: v for k, v in user.items() if k != "password"}
    _log_attempt(username, success=False)
    return None

def get_all_users() -> list[dict]:
    with get_conn() as cur:
        cur.execute(
            "SELECT id,username,nama,role,is_active,created_at,last_login FROM users ORDER BY id"
        )
        return cur.fetchall()

def add_user(username: str, password: str, nama: str, role: str) -> tuple[bool, str]:
    ok, msg = _validate_username(username)
    if not ok: return False, msg
    ok, msg = _validate_password(password)
    if not ok: return False, msg
    if role not in ("admin", "operator"):
        return False, "Role tidak valid."
    try:
        with get_conn() as cur:
            cur.execute(
                "INSERT INTO users (username,password,nama,role) VALUES (%s,%s,%s,%s)",
                (username, _hash(password), nama[:100], role)
            )
        return True, "User berhasil ditambahkan."
    except mysql.connector.IntegrityError:
        return False, f"Username '{username}' sudah digunakan."
    except Exception as e:
        return False, str(e)

def delete_user(username: str) -> bool:
    if username == "admin":
        return False
    try:
        with get_conn() as cur:
            cur.execute(
                "UPDATE users SET is_active=0 WHERE username=%s AND username!='admin'",
                (username,)
            )
        return True
    except Exception:
        return False

def change_password(username: str, old_pw: str, new_pw: str) -> tuple[bool, str]:
    ok, msg = _validate_password(new_pw)
    if not ok: return False, msg
    with get_conn() as cur:
        cur.execute(
            "SELECT id FROM users WHERE username=%s AND password=%s AND is_active=1",
            (username, _hash(old_pw))
        )
        if not cur.fetchone():
            return False, "Password lama salah."
        cur.execute(
            "UPDATE users SET password=%s WHERE username=%s",
            (_hash(new_pw), username)
        )
    return True, "Password berhasil diubah."


# ─────────────────────────────────────────────────────────────────────────────
# PENGENDALIAN MUTU
# ─────────────────────────────────────────────────────────────────────────────
def get_defect_data() -> list[dict]:
    with get_conn() as cur:
        cur.execute(
            "SELECT id,jenis_defect,frekuensi FROM defect_data ORDER BY frekuensi DESC"
        )
        return cur.fetchall()

def save_defect_data(rows: list[dict], updated_by: str = "") -> bool:
    try:
        with get_conn() as cur:
            cur.execute("DELETE FROM defect_data")
            if rows:
                cur.executemany(
                    "INSERT INTO defect_data (jenis_defect,frekuensi,updated_by) VALUES (%s,%s,%s)",
                    [(str(r["Jenis Defect"])[:100], max(0, int(r["Frekuensi"])),
                      updated_by[:30]) for r in rows]
                )
        return True
    except Exception as e:
        logger.error(f"save_defect_data error: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# PERAMALAN
# ─────────────────────────────────────────────────────────────────────────────
def get_demand_history(produk: str = None) -> list[dict]:
    with get_conn() as cur:
        if produk and produk != "Semua":
            cur.execute(
                "SELECT tanggal,permintaan,produk FROM demand_history WHERE produk=%s ORDER BY tanggal",
                (produk[:100],)
            )
        else:
            cur.execute(
                "SELECT tanggal,permintaan,produk FROM demand_history ORDER BY tanggal"
            )
        return cur.fetchall()

def add_demand_row(tanggal: str, permintaan: int, produk: str, added_by: str = "") -> bool:
    try:
        permintaan = max(0, int(permintaan))
        with get_conn() as cur:
            cur.execute(
                "INSERT INTO demand_history (tanggal,permintaan,produk,added_by) VALUES (%s,%s,%s,%s)",
                (tanggal, permintaan, produk[:100], added_by[:30])
            )
        return True
    except Exception as e:
        logger.error(f"add_demand_row error: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# PREDIKSI SUHU
# ─────────────────────────────────────────────────────────────────────────────
def get_suhu_data(limit: int = 500) -> list[dict]:
    limit = min(max(1, int(limit)), 5000)
    with get_conn() as cur:
        cur.execute(
            "SELECT timestamp,zona1,zona2,zona3,zona4 FROM suhu_data ORDER BY timestamp DESC LIMIT %s",
            (limit,)
        )
        return cur.fetchall()

def insert_suhu_rows(rows: list[dict], added_by: str = "") -> int:
    if not rows:
        return 0
    with get_conn() as cur:
        cur.executemany(
            """INSERT IGNORE INTO suhu_data (timestamp,zona1,zona2,zona3,zona4,added_by)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            [(r["timestamp"], r.get("zona1"), r.get("zona2"),
              r.get("zona3"), r.get("zona4"), added_by[:30]) for r in rows]
        )
        return cur.rowcount


# ─────────────────────────────────────────────────────────────────────────────
# OPTIMASI DISTRIBUSI
# ─────────────────────────────────────────────────────────────────────────────
def get_destinasi(aktif_only: bool = True) -> list[dict]:
    with get_conn() as cur:
        if aktif_only:
            cur.execute(
                "SELECT id,nama,demand,latitude,longitude FROM destinasi WHERE aktif=1 ORDER BY nama"
            )
        else:
            cur.execute(
                "SELECT id,nama,demand,latitude,longitude,aktif FROM destinasi ORDER BY nama"
            )
        return cur.fetchall()

def save_destinasi(rows: list[dict], updated_by: str = "") -> bool:
    try:
        with get_conn() as cur:
            cur.execute("DELETE FROM destinasi")
            if rows:
                cur.executemany(
                    "INSERT INTO destinasi (nama,demand,latitude,longitude,updated_by) VALUES (%s,%s,%s,%s,%s)",
                    [(str(r["Destination"])[:100], max(0, int(r["Demand"])),
                      float(r["Lat"]), float(r["Lon"]), updated_by[:30]) for r in rows]
                )
        return True
    except Exception as e:
        logger.error(f"save_destinasi error: {e}")
        return False

def save_hasil_rute(run_by, n_vehicles, capacity, total_dist, status, routes, params) -> int:
    with get_conn() as cur:
        cur.execute(
            """INSERT INTO hasil_rute
               (run_by,n_vehicles,capacity,total_dist_km,status_solver,routes_json,params_json)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (run_by[:30], int(n_vehicles), int(capacity),
             float(total_dist), str(status)[:50],
             json.dumps(routes), json.dumps(params))
        )
        return cur.lastrowid

def get_riwayat_rute(limit: int = 10) -> list[dict]:
    limit = min(max(1, int(limit)), 100)
    with get_conn() as cur:
        cur.execute(
            """SELECT id,run_at,run_by,n_vehicles,capacity,total_dist_km,status_solver
               FROM hasil_rute ORDER BY run_at DESC LIMIT %s""",
            (limit,)
        )
        return cur.fetchall()
