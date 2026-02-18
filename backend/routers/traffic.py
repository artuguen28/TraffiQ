from typing import Optional
from fastapi import APIRouter, HTTPException
from traffic_counter.database_client import DatabaseClient

router = APIRouter()


@router.get("/summary")
def traffic_summary(
    cam_id: Optional[str] = None,
    from_ts: Optional[str] = None,
    to_ts: Optional[str] = None,
):
    db = DatabaseClient()
    try:
        return db.get_traffic_summary(cam_id=cam_id, from_ts=from_ts, to_ts=to_ts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/live")
def live_traffic():
    db = DatabaseClient()
    try:
        return db.get_live_traffic()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
