from typing import Optional, List
from pydantic import BaseModel


class CameraCreate(BaseModel):
    cam_id: str
    video_path: str
    frame_width: int
    frame_height: int
    lines: List[List[int]]


class CameraResponse(BaseModel):
    cam_id: str
    video_path: str
    lines: List


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    sql_query: Optional[str] = None
    data: Optional[List] = None
