import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        start = time.perf_counter()

        response: Response = await call_next(request)

        latency_ms = (time.perf_counter() - start) * 1000.0

        # Store in request.state for later use
        request.state.request_id = request_id
        request.state.latency_ms = round(latency_ms, 2)

        # Send back to client as headers
        response.headers["x-request-id"] = request_id
        response.headers["x-latency-ms"] = str(round(latency_ms, 2))

        return response
