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

            CREATE TABLE IF NOT EXISTS unknown_questions (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                question   TEXT NOT NULL,
                answered   INTEGER DEFAULT 0,
                ts         DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS visits (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                ip         TEXT,
                country    TEXT,
                region     TEXT,
                city       TEXT,
                ts         DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
    _seed_faq(conn)
    conn.close()


def _seed_faq(conn: sqlite3.Connection) -> None:
    faq_path = Path(__file__).parent / "knowledge_base" / "faq.md"
    if not faq_path.exists():
        return

    text = faq_path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"\*\*Q:\s*(.+?)\*\*\s*\nA:\s*(.+?)(?=\n\*\*Q:|\Z)",
        re.DOTALL,
    )
    rows = []
    for m in pattern.finditer(text):
        question = m.group(1).strip().strip('"')
        answer = m.group(2).strip()
        rows.append((question, answer, "general"))

    if not rows:
        return

    # Always wipe and reseed so faq.md changes take effect on restart
    conn.execute("DELETE FROM faq")
    conn.execute("DELETE FROM faq_fts")
    conn.executemany(
        "INSERT INTO faq (question, answer, category) VALUES (?, ?, ?)", rows
    )
    conn.execute("INSERT INTO faq_fts(faq_fts) VALUES('rebuild')")
    print(f"[db] FAQ seeded — {len(rows)} entries")


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


# ── Unknown questions ────────────────────────────────────────────────────────

def save_unknown_question(question: str, session_id: str = "") -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            "INSERT INTO unknown_questions (session_id, question) VALUES (?, ?)",
            (session_id, question),
        )
    conn.close()


def get_unknown_questions(unanswered_only: bool = False) -> list[dict]:
    conn = get_connection()
    sql = "SELECT id, session_id, question, answered, ts FROM unknown_questions"
    if unanswered_only:
        sql += " WHERE answered = 0"
    sql += " ORDER BY ts DESC"
    rows = conn.execute(sql).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_question_answered(question_id: int) -> None:
    conn = get_connection()
    with conn:
        conn.execute("UPDATE unknown_questions SET answered = 1 WHERE id = ?", (question_id,))
    conn.close()


# ── Lead recording ───────────────────────────────────────────────────────────

def save_visit(session_id: str, ip: str, country: str, region: str, city: str) -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            "INSERT INTO visits (session_id, ip, country, region, city) VALUES (?, ?, ?, ?, ?)",
            (session_id, ip, country, region, city),
        )
    conn.close()


def was_ip_seen_recently(ip: str, minutes: int = 60) -> bool:
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM visits WHERE ip = ? AND ts >= datetime('now', ? || ' minutes') LIMIT 1",
        (ip, f"-{minutes}"),
    ).fetchone()
    conn.close()
    return row is not None


def get_daily_stats() -> dict:
    conn = get_connection()
    visits = conn.execute(
        "SELECT country, city, ts FROM visits WHERE ts >= datetime('now', '-1 day') ORDER BY ts DESC"
    ).fetchall()
    questions = conn.execute(
        "SELECT content, ts FROM conversations WHERE role = 'user' AND ts >= datetime('now', '-1 day') ORDER BY ts DESC"
    ).fetchall()
    unknown = conn.execute(
        "SELECT question FROM unknown_questions WHERE ts >= datetime('now', '-1 day')"
    ).fetchall()
    leads = conn.execute(
        "SELECT name, email FROM leads WHERE ts >= datetime('now', '-1 day')"
    ).fetchall()
    conn.close()

    countries = {}
    for v in visits:
        c = v["country"] or "Unknown"
        countries[c] = countries.get(c, 0) + 1

    return {
        "visit_count": len(visits),
        "unique_ips": len(set(v["city"] for v in visits)),
        "countries": countries,
        "question_count": len(questions),
        "unknown_count": len(unknown),
        "unknown_questions": [u["question"] for u in unknown],
        "new_leads": [{"name": l["name"], "email": l["email"]} for l in leads],
    }


def save_lead(session_id: str, email: str, name: str = "", notes: str = "") -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            "INSERT INTO leads (session_id, name, email, notes) VALUES (?, ?, ?, ?)",
            (session_id, name, email, notes),
        )
    conn.close()
