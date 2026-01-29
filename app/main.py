from fastapi import FastAPI
from app.api.routes import router
import contextlib
from app.core.logging import setup_logging
from app.core.middleware import RequestContextMiddleware
from app.core.db import init_db
from app.mcp.math_server import math_mcp

setup_logging()

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    async with math_mcp.session_manager.run():
        yield
        

app = FastAPI(title="AI Engineer Capstone", description="AI Engineer Capstone API", version="0.1.0", lifespan=lifespan)
app.add_middleware(RequestContextMiddleware)
app.include_router(router)

app.mount("/mcp", math_mcp.streamable_http_app())
