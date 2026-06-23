"""
Server minimal de licente: valideaza o cheie si jurnalizeaza device-ul care a
folosit-o (pentru detectia partajarii aceleiasi chei pe mai multe masini).

Endpoint-uri:
  POST /validate  { key, device_id } -> { status: "valid" | "invalid" }
  POST /issue      { key, admin_token } -> emite/reactiveaza o cheie (doar cu ADMIN_TOKEN)
  GET  /devices/{key}  ?admin_token=... -> lista device-urilor care au folosit cheia
  GET  /health     -> { ok: true }
"""

import os
from datetime import datetime, timezone

import libsql
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Baza de date Turso (persistenta reala - tier-ul gratuit Render are disc
# efemer, deci datele NU pot fi tinute pe discul local al serverului).
TURSO_DB_URL = os.environ["TURSO_DB_URL"]
TURSO_DB_TOKEN = os.environ["TURSO_DB_TOKEN"]
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

app = FastAPI()


def get_db():
    conn = libsql.connect(database=TURSO_DB_URL, auth_token=TURSO_DB_TOKEN)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS licenses (
            key TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'valid',
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS device_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_key TEXT NOT NULL,
            device_id TEXT NOT NULL,
            seen_at TEXT NOT NULL
        )
        """
    )
    return conn


def require_admin(token):
    if not ADMIN_TOKEN or token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")


class ValidateRequest(BaseModel):
    key: str
    device_id: str


class IssueRequest(BaseModel):
    key: str
    admin_token: str


@app.post("/validate")
def validate(req: ValidateRequest):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT status FROM licenses WHERE key = ?", (req.key,)
        ).fetchone()

        conn.execute(
            "INSERT INTO device_log (license_key, device_id, seen_at) VALUES (?, ?, ?)",
            (req.key, req.device_id, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()

        if row is None:
            return {"status": "invalid"}
        return {"status": row[0]}
    finally:
        conn.close()


@app.post("/issue")
def issue(req: IssueRequest):
    require_admin(req.admin_token)
    conn = get_db()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO licenses (key, status, created_at) VALUES (?, 'valid', ?)",
            (req.key, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        return {"status": "issued", "key": req.key}
    finally:
        conn.close()


@app.get("/devices/{key}")
def devices(key: str, admin_token: str):
    require_admin(admin_token)
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT device_id, seen_at FROM device_log WHERE license_key = ? ORDER BY seen_at DESC",
            (key,),
        ).fetchall()
        return {"key": key, "devices": [{"device_id": d, "seen_at": s} for d, s in rows]}
    finally:
        conn.close()


@app.get("/health")
def health():
    return {"ok": True}
