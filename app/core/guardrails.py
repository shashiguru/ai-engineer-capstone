import re
from app.core.tool_schemas import MAX_ABS_INT

UNSAFE_PATTERNS = [
    "ignore previous instructions",
    "system prompt",
    "developer message",
    "reveal hidden",
    "exfiltrate",
    "steal",
    "delete",
    "drop table"
]

def is_unsafe_user_input(text: str) -> bool:
    t = text.lower()
    if any(p in t for p in UNSAFE_PATTERNS):
        return True

    if re.search(r"\b(ignore|bypass|override)\b.*\b(instructions|rules|policy)\b", t):
        return True

    # Block overly large integers to avoid tool validation errors
    for match in re.findall(r"-?\d+", t):
        try:
            if abs(int(match)) > MAX_ABS_INT:
                return True
        except ValueError:
            continue

    return False