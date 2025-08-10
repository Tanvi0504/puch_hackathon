# whatsappbot/db.py
import sqlite3
from pathlib import Path
from typing import List, Optional

# DB file at project root: <project>/tasks.db
DB_PATH = Path(__file__).resolve().parent.parent / "tasks.db"

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Create tables/indexes if they don't exist."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            scope TEXT NOT NULL,                 -- 'today' | 'week' | 'month'
            text  TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open', -- 'open' | 'done'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_phone ON tasks(phone)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_phone_status ON tasks(phone, status)")
    conn.commit()
    conn.close()

def add_task(phone: str, scope: str, text: str) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (phone, scope, text) VALUES (?, ?, ?)",
        (phone, scope, text),
    )
    conn.commit()
    task_id = cur.lastrowid
    conn.close()
    return task_id

def list_tasks(phone: str, scope: Optional[str] = None) -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    if scope:
        cur.execute(
            "SELECT * FROM tasks WHERE phone=? AND scope=? AND status='open' ORDER BY id DESC",
            (phone, scope),
        )
    else:
        cur.execute(
            "SELECT * FROM tasks WHERE phone=? AND status='open' ORDER BY id DESC",
            (phone,),
        )
    rows = cur.fetchall()
    conn.close()
    return rows

def complete_task(phone: str, task_text_or_id: str) -> int:
    conn = get_conn()
    cur = conn.cursor()
    if task_text_or_id.isdigit():
        cur.execute(
            "UPDATE tasks SET status='done' WHERE phone=? AND id=?",
            (phone, int(task_text_or_id)),
        )
    else:
        cur.execute(
            "UPDATE tasks SET status='done' WHERE phone=? AND text LIKE ? LIMIT 1",
            (phone, f"%{task_text_or_id}%"),
        )
    conn.commit()
    count = cur.rowcount
    conn.close()
    return count

def delete_task(phone: str, task_text_or_id: str) -> int:
    conn = get_conn()
    cur = conn.cursor()
    if task_text_or_id.isdigit():
        cur.execute(
            "DELETE FROM tasks WHERE phone=? AND id=?",
            (phone, int(task_text_or_id)),
        )
    else:
        cur.execute(
            "DELETE FROM tasks WHERE phone=? AND text LIKE ? LIMIT 1",
            (phone, f"%{task_text_or_id}%"),
        )
    conn.commit()
    count = cur.rowcount
    conn.close()
    return count
