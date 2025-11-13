import math
import time

class LaneCounter:
    def __init__(self, camera):
        self.camera = camera
        self.counts = [0] * len(camera.lanes)
        self.interval_counts = [0] * len(camera.lanes)
        self.passed_ids = [set() for _ in camera.lanes]
        self.last_save_time = time.time()
        self.max_cars_in_frame = 0

    @staticmethod
    def _point_to_segment_distance(px, py, x1, y1, x2, y2):
        """Compute shortest distance from point (px, py) to line segment (x1,y1)-(x2,y2)."""
        line_mag = math.hypot(x2 - x1, y2 - y1)
        if line_mag < 1e-6:
            return math.hypot(px - x1, py - y1)

        # Projection factor t of point on line
        t = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / (line_mag ** 2)
        t = max(0, min(1, t))
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)
        return math.hypot(px - proj_x, py - proj_y)

    def update_counts(self, tracks, threshold=15):
        """Generalized count update for arbitrary line orientations."""
        active_cars = len([t for t in tracks if t.is_confirmed()])
        self.max_cars_in_frame = max(self.max_cars_in_frame, active_cars)

        for t in tracks:
            if not t.is_confirmed():
                continue
            x1, y1, x2, y2 = map(int, t.to_ltrb())
            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)

            for i, (lx1, ly1, lx2, ly2) in enumerate(self.camera.lanes):
                dist = self._point_to_segment_distance(cx, cy, lx1, ly1, lx2, ly2)
                if dist <= threshold:
                    if t.track_id not in self.passed_ids[i]:
                        self.passed_ids[i].add(t.track_id)
                        self.counts[i] += 1
                        self.interval_counts[i] += 1

        return self.counts

    def periodic_save(self, db_client=None, interval=10):
        now = time.time()
        if now - self.last_save_time >= interval:
            if db_client:
                db_client.save_interval(self.camera.id, self.interval_counts, self.max_cars_in_frame)
            self.interval_counts = [0] * len(self.camera.lanes)
            self.max_cars_in_frame = 0
            self.last_save_time = now
            return True
        return False
