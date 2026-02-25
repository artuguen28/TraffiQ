import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import cameras, traffic, counter, rag
from backend.counter_worker import CounterWorker
from backend.auth import verify_api_key

app = FastAPI(title="TraffiQ API")

# ---------------------------------------------------------------------------
# CORS — restrict to known origins.
# Override ALLOWED_ORIGINS in .env for production (comma-separated list).
# ---------------------------------------------------------------------------
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:7860")
allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.worker = CounterWorker()

_auth = [Depends(verify_api_key)]

app.include_router(cameras.router, prefix="/cameras", tags=["cameras"], dependencies=_auth)
app.include_router(traffic.router, prefix="/traffic", tags=["traffic"], dependencies=_auth)
app.include_router(counter.router, prefix="/counter", tags=["counter"], dependencies=_auth)
app.include_router(rag.router, prefix="/rag", tags=["rag"], dependencies=_auth)


@app.get("/")
def root():
    return {"message": "TraffiQ API", "docs": "/docs"}
