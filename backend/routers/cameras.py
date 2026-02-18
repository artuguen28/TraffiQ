from fastapi import APIRouter, HTTPException
from backend.models import CameraCreate, CameraResponse
from traffic_counter.database_client import DatabaseClient

router = APIRouter()


@router.get("", response_model=list[CameraResponse])
def list_cameras():
    db = DatabaseClient()
    try:
        return db.get_registered_cameras()
    finally:
        db.close()


@router.post("", status_code=201)
def register_camera(camera: CameraCreate):
    db = DatabaseClient()
    try:
        db.save_camera(
            cam_id=camera.cam_id,
            video_path=camera.video_path,
            frame_width=camera.frame_width,
            frame_height=camera.frame_height,
            lines=camera.lines,
        )
        return {"registered": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.delete("/{cam_id}")
def delete_camera(cam_id: str):
    db = DatabaseClient()
    try:
        db.delete_camera(cam_id)
        return {"deleted": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
