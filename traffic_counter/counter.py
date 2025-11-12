import time

class LaneCounter:
    def __init__(self, lanes, line_y):
        self.lane_regions = lanes
        self.line_y = line_y
        self.counts = [0] * len(lanes)
        self.passed_ids = [set() for _ in lanes]
        self.last_save_time = time.time()

    def update_counts(self, tracks):
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
        return self.counts

    def periodic_save(self, db_client=None, interval=10):
        now = time.time()
        if now - self.last_save_time >= interval:
            self.last_save_time = now
            if db_client:
                db_client.save_counts(self.counts)
            return True
        return False