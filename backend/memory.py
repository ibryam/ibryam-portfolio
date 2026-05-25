import sqlite3
import os
import re
from pathlib import Path

DB_PATH = os.getenv("DB_PATH", "ibryam_chat.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    with conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role      TEXT NOT NULL,
                content   TEXT NOT NULL,
                ts        DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id, ts);

            CREATE TABLE IF NOT EXISTS faq (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer   TEXT NOT NULL,
                category TEXT DEFAULT 'general'
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS faq_fts
                USING fts5(question, answer, content='faq', content_rowid='id');

            CREATE TABLE IF NOT EXISTS leads (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                name       TEXT,
                email      TEXT NOT NULL,
                notes      TEXT,
                ts         DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
    _seed_faq(conn)
    conn.close()


def _seed_faq(conn: sqlite3.Connection) -> None:
    count = conn.execute("SELECT COUNT(*) FROM faq").fetchone()[0]
    if count > 0:
        return

    faq_path = Path(__file__).parent / "knowledge_base" / "faq.md"
    if not faq_path.exists():
        return

    text = faq_path.read_text(encoding="utf-8")
    # Parse Q/A blocks: **Q: ...** / A: ...
    pattern = re.compile(
        r"\*\*Q:\s*(.+?)\*\*\s*\nA:\s*(.+?)(?=\n\*\*Q:|\Z)",
        re.DOTALL,
    )
    rows = []
    for m in pattern.finditer(text):
        question = m.group(1).strip()
        answer = m.group(2).strip()
        rows.append((question, answer, "general"))

    if rows:
        conn.executemany(
            "INSERT INTO faq (question, answer, category) VALUES (?, ?, ?)", rows
        )
        conn.execute("INSERT INTO faq_fts(faq_fts) VALUES('rebuild')")


# ── Conversation memory ──────────────────────────────────────────────────────

def save_message(session_id: str, role: str, content: str) -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            "INSERT INTO conversations (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )
    conn.close()


def get_recent_history(session_id: str, limit: int = 10) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT role, content FROM conversations
           WHERE session_id = ?
           ORDER BY ts DESC LIMIT ?""",
        (session_id, limit),
    ).fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


# ── FAQ lookup ───────────────────────────────────────────────────────────────

def search_faq(query: str, limit: int = 3) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT f.question, f.answer
           FROM faq_fts ft
           JOIN faq f ON f.id = ft.rowid
           WHERE faq_fts MATCH ?
           ORDER BY rank
           LIMIT ?""",
        (query, limit),
    ).fetchall()
    conn.close()
    return [{"question": r["question"], "answer": r["answer"]} for r in rows]


# ── Lead recording ───────────────────────────────────────────────────────────

def save_lead(session_id: str, email: str, name: str = "", notes: str = "") -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            "INSERT INTO leads (session_id, name, email, notes) VALUES (?, ?, ?, ?)",
            (session_id, name, email, notes),
        )
    conn.close()
