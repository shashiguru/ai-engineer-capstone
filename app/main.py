from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="AI Engineer Capstone", description="AI Engineer Capstone API", version="0.1.0")

app.include_router(router)
