import cv2
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort


class VehicleTracker:
    def __init__(self, model_path, device="cuda"):
        self.model = YOLO(model_path)
        self.model.to(device)
        self.tracker = DeepSort(
            max_iou_distance=0.8,  # lenient matching helps border vehicles
            max_age=8,            # ~1s at 30fps before a lost track is deleted
            n_init=3,              # confirmed after 2 consecutive hits
            nms_max_overlap=0.5    # balanced: suppresses near-duplicates without killing close vehicles
        )

    def detect_and_track(self, frame):
        h, w = frame.shape[:2]
        results = self.model.predict(source=frame, conf=0.3, iou=0.6, verbose=False)
        detections = []

        for result in results:
            for box in result.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(float, box.xyxy[0].tolist())

                if x2 <= x1 or y2 <= y1 or cls not in [2, 5, 7] or conf < 0.4:
                    continue

                # Clip to frame bounds — normalises partial detections at all borders
                x1, y1 = max(0.0, x1), max(0.0, y1)
                x2, y2 = min(float(w), x2), min(float(h), y2)

                bw, bh = x2 - x1, y2 - y1

                # Frame-relative size gate: skip degenerate or unrealistically large boxes
                if bw < 5 or bh < 5 or bw > w * 0.45 or bh > h * 0.5:
                    continue

                bbox_xywh = [x1, y1, bw, bh]
                detections.append((bbox_xywh, conf, "car"))

        tracks = self.tracker.update_tracks(detections, frame=frame)

        # Post-track filters applied only to confirmed tracks
        valid = []
        for t in tracks:
            if t.is_confirmed():
                x1, y1, x2, y2 = t.to_ltrb()
                bw, bh = x2 - x1, y2 - y1
                # Drop tracks whose Kalman-predicted bbox grew unreasonably large
                if bw > w * 0.5 or bh > h * 0.6:
                    continue
            valid.append(t)

        return self._suppress_duplicate_tracks(valid)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _iou(a, b):
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b
        ix1, iy1 = max(ax1, bx1), max(ay1, by1)
        ix2, iy2 = min(ax2, bx2), min(ay2, by2)
        inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
        if inter == 0.0:
            return 0.0
        area_a = (ax2 - ax1) * (ay2 - ay1)
        area_b = (bx2 - bx1) * (by2 - by1)
        return inter / (area_a + area_b - inter)

    def _suppress_duplicate_tracks(self, tracks, iou_threshold=0.5):
        """NMS over confirmed tracks: when two overlap, keep the older (lower ID) one."""
        confirmed = [i for i, t in enumerate(tracks) if t.is_confirmed()]
        suppress = set()

        for a in range(len(confirmed)):
            i = confirmed[a]
            if i in suppress:
                continue
            box_a = tracks[i].to_ltrb()
            for b in range(a + 1, len(confirmed)):
                j = confirmed[b]
                if j in suppress:
                    continue
                box_b = tracks[j].to_ltrb()
                if self._iou(box_a, box_b) > iou_threshold:
                    # Suppress whichever track was created more recently
                    newer = i if tracks[i].track_id > tracks[j].track_id else j
                    suppress.add(newer)

        return [t for i, t in enumerate(tracks) if i not in suppress]
