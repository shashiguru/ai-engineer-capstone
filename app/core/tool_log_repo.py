import json
from sqlalchemy import text
from app.core.db import engine


def insert_tool_log(
    request_id: str,
    tool_name: str,
    args_hash: str,
    args: dict,
    tool_latency_ms: float,
    tool_output_preview: str,
    success: bool,
    error: str | None = None,
) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO tool_logs
            (request_id, tool_name, args_hash, args_json, tool_latency_ms, tool_output_preview, success, error)
            VALUES
            (:request_id, :tool_name, :args_hash, :args_json, :tool_latency_ms, :tool_output_preview, :success, :error)
            """),
            {
                "request_id": request_id,
                "tool_name": tool_name,
                "args_hash": args_hash,
                "args_json": json.dumps(args, ensure_ascii=False),
                "tool_latency_ms": tool_latency_ms,
                "tool_output_preview": tool_output_preview[:200],
                "success": 1 if success else 0,
                "error": error,
            },
        )