import argparse
import cv2
from tracker import VehicleTracker
from counter import LaneCounter
from visualizer import Visualizer
from database_client import DatabaseClient

def main(model_path, input_path, output_path):
    tracker = VehicleTracker(model_path)
    line_y = 1000
    lane_regions = [(0, 650), (800, 1100), (1200, 1600)]
    counter = LaneCounter(lane_regions, line_y, "0001")
    db_client = DatabaseClient()

    visualizer = Visualizer(line_y, lane_regions)

    cap = cv2.VideoCapture(input_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        tracks = tracker.detect_and_track(frame)
        counts = counter.update_counts(tracks)

        frame = visualizer.draw_lines(frame)
        frame = visualizer.draw_tracks(frame, tracks)
        frame = visualizer.draw_counts(frame, counts)

        writer.write(frame)

        

        if counter.periodic_save(interval=7, db_client=db_client):
            print(f"[SAVE] Counts at {frame_count/fps:.1f}s → {counts}")

        frame_count += 1
        if frame_count % 30 == 0:
            print(f"Processed {frame_count} frames...")

    db_client.close()

    cap.release()
    writer.release()
    print(f"Final lane counts: {counter.counts}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="tracked_output.mp4")
    args = parser.parse_args()
    main(args.model, args.input, args.output)