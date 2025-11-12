import argparse
import cv2
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

def draw_tracks(frame, tracks):
    for t in tracks:
        x1, y1, x2, y2 = map(int, t.to_ltrb())
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"ID {t.track_id}", (x1, max(20, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
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

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Run inference on original frame
        results = model.predict(source=frame, conf=0.5, iou=0.8, verbose=False)

        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(float, box.xyxy[0].tolist())

                # sanity: skip bad boxes
                if x2 <= x1 or y2 <= y1:
                    continue

                # Only car-like classes (COCO): 2=car, 5=bus, 7=truck
                if cls not in [2, 5, 7] or conf < 0.4:
                    continue

                # Convert xyxy -> xywh (DeepSORT expects left,top,width,height)
                bw = x2 - x1
                bh = y2 - y1
                bbox_xywh = [x1, y1, bw, bh]

                # append in DeepSORT expected format: (bbox, confidence, class)
                detections.append((bbox_xywh, conf, "car"))

        # Update DeepSORT tracker
        tracks = tracker.update_tracks(detections, frame=frame)
        frame = draw_tracks(frame, tracks)

        writer.write(frame)
        frame_count += 1

        if frame_count % 30 == 0:
            print(f"Processed {frame_count} frames...")

    cap.release()
    writer.release()
    print(f"Tracking complete. Output saved to: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Path to YOLOv12m .pt model")
    parser.add_argument("--input", required=True, help="Input video path")
    parser.add_argument("--output", default="tracked_output.mp4", help="Output video path")
    args = parser.parse_args()
    main(args.model, args.input, args.output)
