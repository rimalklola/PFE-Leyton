import os
import sqlite3
import uuid
from datetime import datetime, timedelta

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(_PROJECT_ROOT, "runs.db")


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id          TEXT PRIMARY KEY,
                service     TEXT NOT NULL,
                client_id   TEXT,
                status      TEXT NOT NULL,
                output_file TEXT,
                duration_ms INTEGER,
                error_message TEXT,
                ran_at      TEXT NOT NULL
            )
        """)
        conn.commit()


_init_db()


def log_run(service_name, client_id=None, status="success",
            output_file=None, duration_ms=None, error_message=None):
    run_id = str(uuid.uuid4())
    ran_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO runs (id, service, client_id, status, output_file, duration_ms, error_message, ran_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (run_id, service_name, client_id, status, output_file, duration_ms, error_message, ran_at),
        )
        conn.commit()
    return run_id


def get_runs(service_name=None, client_id=None, since_days=30):
    since = (datetime.utcnow() - timedelta(days=since_days)).strftime("%Y-%m-%dT%H:%M:%S")
    query = "SELECT * FROM runs WHERE ran_at >= ?"
    params = [since]
    if service_name:
        query += " AND service = ?"
        params.append(service_name)
    if client_id:
        query += " AND client_id = ?"
        params.append(client_id)
    query += " ORDER BY ran_at DESC"
    with _get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_last_run(service_name, client_id=None):
    query = "SELECT * FROM runs WHERE service = ?"
    params = [service_name]
    if client_id:
        query += " AND client_id = ?"
        params.append(client_id)
    query += " ORDER BY ran_at DESC LIMIT 1"
    with _get_conn() as conn:
        row = conn.execute(query, params).fetchone()
    return dict(row) if row else None


def was_run_this_month(service_name, client_id=None):
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0).strftime("%Y-%m-%dT%H:%M:%S")
    query = "SELECT COUNT(*) FROM runs WHERE service = ? AND status = 'success' AND ran_at >= ?"
    params = [service_name, month_start]
    if client_id:
        query += " AND client_id = ?"
        params.append(client_id)
    with _get_conn() as conn:
        count = conn.execute(query, params).fetchone()[0]
    return count > 0
