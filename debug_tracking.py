"""
Debug script for detection and tracking visualization.
No database, no counting — just bboxes on screen.

Usage:
    python debug_tracking.py <video_path> [--model MODEL_PATH] [--speed SPEED]

Controls:
    q      quit
    space  pause / resume
    s      step one frame while paused
"""
import argparse
import sys
import time
import cv2
from traffic_counter.tracker import VehicleTracker


def parse_args():
    parser = argparse.ArgumentParser(description="Debug tracking on a video file.")
    parser.add_argument("video", help="Path to the input video file")
    parser.add_argument("--model", default="model/yolo26l.pt", help="Path to YOLO model weights")
    parser.add_argument(
        "--speed", type=float, default=1.0,
        help="Playback speed multiplier (e.g. 0.5 = half speed, 2.0 = double speed)"
    )
    return parser.parse_args()


def draw_tracks(frame, tracks):
    for t in tracks:
        if not t.is_confirmed():
            continue
        x1, y1, x2, y2 = map(int, t.to_ltrb())
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
        cv2.putText(frame, f"id:{t.track_id}", (x1, y1 - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)


def draw_overlay(frame, frame_idx, fps, n_tracks, paused):
    status = "PAUSED" if paused else f"{fps:.1f} fps"
    cv2.putText(frame, f"frame {frame_idx}  |  tracks: {n_tracks}  |  {status}",
                (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)


def main():
    args = parse_args()

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        sys.exit(f"[ERROR] Cannot open video: {args.video}")

    video_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_delay = 1.0 / (video_fps * args.speed)

    print(f"[INFO] Video: {args.video}")
    print(f"[INFO] Model: {args.model}")
    print(f"[INFO] Video FPS: {video_fps:.1f}  |  Speed: {args.speed}x")
    print("[INFO] Loading model...")

    tracker = VehicleTracker(args.model)

    print("[INFO] Ready. Press 'q' to quit, space to pause, 's' to step.")
    cv2.namedWindow("debug_tracking", cv2.WINDOW_NORMAL)

    paused = False
    frame_idx = 0
    fps_display = 0.0
    t_prev = time.time()

    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                print("[INFO] End of video.")
                break

            tracks = tracker.detect_and_track(frame)
            confirmed = [t for t in tracks if t.is_confirmed()]

            # FPS smoothing
            t_now = time.time()
            fps_display = 0.9 * fps_display + 0.1 * (1.0 / max(t_now - t_prev, 1e-6))
            t_prev = t_now

            draw_tracks(frame, tracks)
            draw_overlay(frame, frame_idx, fps_display, len(confirmed), paused)
            cv2.imshow("debug_tracking", frame)
            frame_idx += 1

        else:
            # Redraw overlay with PAUSED status without advancing
            draw_overlay(frame, frame_idx, fps_display, len(confirmed), paused)
            cv2.imshow("debug_tracking", frame)

        # Keyboard handling — waitKey in ms, capped at 1 to keep UI responsive
        wait_ms = max(1, int(frame_delay * 1000)) if not paused else 50
        key = cv2.waitKey(wait_ms) & 0xFF

        if key == ord('q'):
            break
        elif key == ord(' '):
            paused = not paused
        elif key == ord('s') and paused:
            # Step one frame
            ret, frame = cap.read()
            if not ret:
                print("[INFO] End of video.")
                break
            tracks = tracker.detect_and_track(frame)
            confirmed = [t for t in tracks if t.is_confirmed()]
            draw_tracks(frame, tracks)
            draw_overlay(frame, frame_idx, fps_display, len(confirmed), paused)
            cv2.imshow("debug_tracking", frame)
            frame_idx += 1

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
