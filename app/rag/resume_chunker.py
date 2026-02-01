from typing import List


def is_heading(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if s.endswith(":"):
        return True
    # common resume heading style
    if len(s) <= 40 and s.upper() == s and any(c.isalpha() for c in s):
        return True
    return False


def chunk_resume(text: str, max_chars: int = 900) -> List[str]:
    lines = [l.rstrip() for l in text.splitlines()]
    blocks: List[str] = []

    current_heading = ""
    current = []

    def flush():
        nonlocal current, current_heading
        if current:
            body = "\n".join(current).strip()
            if current_heading:
                blocks.append((current_heading + "\n" + body).strip())
            else:
                blocks.append(body)
        current = []

    for line in lines:
        if is_heading(line):
            flush()
            current_heading = line.strip()
        else:
            if line.strip():
                current.append(line)

        # if block becomes too big, flush
        if sum(len(x) for x in current) + len(current_heading) > max_chars:
            flush()

    flush()

    # final safety: if any block still large, split hard
    final: List[str] = []
    for b in blocks:
        if len(b) <= max_chars:
            final.append(b)
        else:
            for i in range(0, len(b), max_chars):
                final.append(b[i : i + max_chars].strip())
    return [x for x in final if x]