class Camera:
    def __init__(self, cam_id, lanes, camera_video, detection_output):
        """
        cam_id: unique camera identifier
        lanes: list of tuples [(x1, y1, x2, y2), ...]
            where (x1, y1) and (x2, y2) define the counting line segment.
        """
        self.id = cam_id
        self.lanes = lanes
        self.camera_video = camera_video
        self.detection_output = detection_output