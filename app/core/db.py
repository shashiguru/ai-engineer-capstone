from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///./app_logs.db", future=True)


def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT,
            message TEXT,
            model TEXT,
            latency_ms REAL,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            total_tokens INTEGER,
            success INTEGER,
            error TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS tool_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT,
            tool_name TEXT,
            args_hash TEXT,
            args_json TEXT,
            tool_latency_ms REAL,
            tool_output_preview TEXT,
            success INTEGER,
            error TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """))