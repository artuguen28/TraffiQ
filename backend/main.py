from fastapi import FastAPI
from backend.routers import cameras, traffic, counter, rag
from backend.counter_worker import CounterWorker

app = FastAPI(title="TraffiQ API")
app.state.worker = CounterWorker()

app.include_router(cameras.router, prefix="/cameras", tags=["cameras"])
app.include_router(traffic.router, prefix="/traffic", tags=["traffic"])
app.include_router(counter.router, prefix="/counter", tags=["counter"])
app.include_router(rag.router, prefix="/rag", tags=["rag"])


@app.get("/")
def root():
    return {"message": "TraffiQ API", "docs": "/docs"}
