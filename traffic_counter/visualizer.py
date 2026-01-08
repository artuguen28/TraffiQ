import cv2

class Visualizer:
    def __init__(self, lanes):
        self.lanes = lanes

    def draw_lines(self, frame):
        for (x1, y1, x2, y2) in self.lanes:
            cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        return frame

    def draw_tracks(self, frame, tracks):
        for t in tracks:
            if not t.is_confirmed():
                continue
            x1, y1, x2, y2 = map(int, t.to_ltrb())
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
        return frame

    def draw_counts(self, frame, counts):
        for i, count in enumerate(counts):
            cv2.putText(frame, f"Line {i+1}: {count}", (50, 50 + i * 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        return frame
