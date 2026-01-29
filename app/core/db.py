from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///./app_logs.db")


def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT,
            message TEXT,
            model TEXT,
            latency_ms REAL,
            success INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """))
