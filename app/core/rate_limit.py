import time
from collections import defaultdict, deque

# Simple in-memory limiter: N requests per window seconds, per key
class RateLimiter:
    def __init__(self, max_requests: int = 2, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.events = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.time()
        q = self.events[key]

        # remove old timestamps
        while q and (now - q[0]) > self.window_seconds:
            q.popleft()

        if len(q) >= self.max_requests:
            return False

        q.append(now)
        return True