import cv2

class Visualizer:
    def __init__(self, line_y, lanes):
        self.line_y = line_y
        self.lanes = lanes

    def draw_lines(self, frame):
        for (x_min, x_max) in self.lanes:
            cv2.line(frame, (x_min, self.line_y), (x_max, self.line_y), (0, 0, 255), 3)
        return frame

    def draw_tracks(self, frame, tracks):
        for t in tracks:
            x1, y1, x2, y2 = map(int, t.to_ltrb())
            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"ID {t.track_id}", (x1, max(20, y1 - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 4, (255, 0, 0), -1)
        return frame

    def draw_counts(self, frame, counts):
        for i, c in enumerate(counts):
            x_pos = self.lanes[i][0] + 10
            y_pos = self.line_y - 20
            cv2.putText(frame, f"{c}", (x_pos, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        return frame