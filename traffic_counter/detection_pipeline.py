import cv2

from .camera import Camera
from .counter import LaneCounter
from .tracker import VehicleTracker
from .visualizer import Visualizer


class CameraPipeline:
    """Encapsulates all components and state for one camera."""
    def __init__(self, camera: Camera, model_path: str):
        self.camera = camera
        self.tracker = VehicleTracker(model_path)
        self.counter = LaneCounter(camera)
        self.visualizer = Visualizer(camera.lanes)

        # Video setup
        self.cap = cv2.VideoCapture(camera.camera_video)
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.writer = cv2.VideoWriter(
            camera.detection_output,
            cv2.VideoWriter_fourcc(*'mp4v'),
            self.fps,
            (self.width, self.height)
        )

    def process_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return False

        tracks = self.tracker.detect_and_track(frame)
        counts = self.counter.update_counts(tracks)

        frame = self.visualizer.draw_lines(frame)
        frame = self.visualizer.draw_tracks(frame, tracks)
        frame = self.visualizer.draw_counts(frame, counts)
        self.writer.write(frame)
        return True

    def cleanup(self):
        self.cap.release()
        self.writer.release()