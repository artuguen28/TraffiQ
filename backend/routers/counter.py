from fastapi import APIRouter, Request

router = APIRouter()


@router.post("/start")
def start_counter(request: Request):
    started = request.app.state.worker.start()
    return {"started": started}


@router.post("/stop")
def stop_counter(request: Request):
    stopped = request.app.state.worker.stop()
    return {"stopped": stopped}


@router.get("/status")
def counter_status(request: Request):
    return {"running": request.app.state.worker.is_running()}
