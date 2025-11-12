import argparse
import cv2
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

def draw_tracks(frame, tracks):
    for t in tracks:
        x1, y1, x2, y2 = map(int, t.to_ltrb())
        cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"ID {t.track_id}", (x1, max(20, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        # Draw centroid
        cv2.circle(frame, (cx, cy), 4, (255, 0, 0), -1)
    return frame

def draw_counting_lines(frame):
    cv2.line(frame, (0, 1000), (650, 1000), (0, 0, 255), 3)
    cv2.line(frame, (800, 1000), (1100, 1000), (0, 0, 255), 3)
    cv2.line(frame, (1200, 1000), (1600, 1000), (0, 0, 255), 3)
    return frame

def main(model_path, input_path, output_path):
    model = YOLO(model_path)
    model.to("cuda")
    print(f"Loaded model: {model_path}")

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print("Error: cannot open input video.")
        return

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))

    tracker = DeepSort(max_age=30)

    # Lane line Y position (same for all 3 lines in this case)
    line_y = 1000
    lane_regions = [(0, 650), (800, 1100), (1200, 1600)]  # x ranges for 3 lanes
    counts = [0, 0, 0]
    passed_ids = [set(), set(), set()]  # one set per lane

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model.predict(source=frame, conf=0.5, iou=0.8, verbose=False)

        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(float, box.xyxy[0].tolist())

                if x2 <= x1 or y2 <= y1:
                    continue
                if cls not in [2, 5, 7] or conf < 0.4:
                    continue

                bw, bh = x2 - x1, y2 - y1
                bbox_xywh = [x1, y1, bw, bh]
                detections.append((bbox_xywh, conf, "car"))

        tracks = tracker.update_tracks(detections, frame=frame)
        frame = draw_counting_lines(frame)
        frame = draw_tracks(frame, tracks)

        for t in tracks:
            if not t.is_confirmed():
                continue
            x1, y1, x2, y2 = map(int, t.to_ltrb())
            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)

            for i, (x_min, x_max) in enumerate(lane_regions):
                if x_min <= cx <= x_max and cy > line_y - 15 and cy < line_y + 15:
                    if t.track_id not in passed_ids[i]:
                        passed_ids[i].add(t.track_id)
                        counts[i] += 1
                        print(f"Lane {i+1} count: {counts[i]}")

        # Display counts on frame
        for i, c in enumerate(counts):
            cv2.putText(frame, f"Lane {i+1}: {c}", (1600, 50 + i * 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        writer.write(frame)
        frame_count += 1
        if frame_count % 30 == 0:
            print(f"Processed {frame_count} frames...")

    cap.release()
    writer.release()
    print(f"Tracking complete. Output saved to: {output_path}")
    print(f"Final counts per lane: {counts}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Path to YOLOv8/YOLOv12 .pt model")
    parser.add_argument("--input", required=True, help="Input video path")
    parser.add_argument("--output", default="tracked_output.mp4", help="Output video path")
    args = parser.parse_args()
    main(args.model, args.input, args.output)
