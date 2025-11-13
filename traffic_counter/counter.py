import time


class LaneCounter:
    def __init__(self, lanes, line_y, cam_id):
        self.lane_regions = lanes
        self.line_y = line_y
        self.cam_id = cam_id
        self.counts = [0] * len(lanes)
        self.interval_counts = [0] * len(lanes)
        self.passed_ids = [set() for _ in lanes]
        self.last_save_time = time.time()
        self.max_cars_in_frame = 0

    def update_counts(self, tracks):
        """Update counts and track max cars visible."""
        active_cars = len([t for t in tracks if t.is_confirmed()])
        self.max_cars_in_frame = max(self.max_cars_in_frame, active_cars)

        for t in tracks:
            if not t.is_confirmed():
                continue
            x1, y1, x2, y2 = map(int, t.to_ltrb())
            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)

            for i, (x_min, x_max) in enumerate(self.lane_regions):
                if x_min <= cx <= x_max and self.line_y - 15 < cy < self.line_y + 15:
                    if t.track_id not in self.passed_ids[i]:
                        self.passed_ids[i].add(t.track_id)
                        self.counts[i] += 1
                        self.interval_counts[i] += 1
        return self.counts

    def periodic_save(self, db_client=None, interval=10):
        now = time.time()
        if now - self.last_save_time >= interval:
            if db_client:
                db_client.save_interval(self.cam_id, self.interval_counts, self.max_cars_in_frame)
            # Reset interval stats
            self.interval_counts = [0] * len(self.lane_regions)
            self.max_cars_in_frame = 0
            self.last_save_time = now
            return True
        return False