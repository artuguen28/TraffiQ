import cv2
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort



class VehicleTracker:
    def __init__(self, model_path, device="cuda"):
        self.model = YOLO(model_path)
        self.model.to(device)
        self.tracker = DeepSort(
            max_iou_distance=0.4,
            max_age=8,
            n_init=3,
            nms_max_overlap=0.3
        )

    def detect_and_track(self, frame):
        results = self.model.predict(source=frame, conf=0.4, iou=0.6, verbose=False)
        detections = []

        for result in results:
            for box in result.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(float, box.xyxy[0].tolist())

                if x2 <= x1 or y2 <= y1 or cls not in [2, 5, 7] or conf < 0.4:
                    continue

                bw, bh = x2 - x1, y2 - y1
                # Skip detections that are too large

                if bw > 300 or bh > 400:
                    continue

                bbox_xywh = [x1, y1, bw, bh]
                detections.append((bbox_xywh, conf, "car"))

        return self.tracker.update_tracks(detections, frame=frame)
    
    
