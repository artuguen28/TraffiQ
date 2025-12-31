import os
import time
from camera import Camera
from database_client import DatabaseClient
from detection_pipeline import CameraPipeline

def main():
    model_path = "model/yolo12l.pt"
    output_dir = "output_videos"
    os.makedirs(output_dir, exist_ok=True)

    # --- Initialize database client ---
    db_client = DatabaseClient()

    # --- Get registered cameras from the database ---
    cameras_data = db_client.get_registered_cameras()  # you need to implement this method
    # Expected to return a list of dicts with keys: cam_id, video_path, lines

    cameras = []
    for cam_data in cameras_data:
        cam_id = cam_data["cam_id"]
        lanes = cam_data["lines"]  # assuming stored as list of tuples: [(x1,y1,x2,y2), ...]
        video_path = cam_data["video_path"]
        detection_output = os.path.join(output_dir, f"{cam_id}.mp4")
        cameras.append(Camera(
            cam_id=cam_id,
            lanes=lanes,
            camera_video=video_path,
            detection_output=detection_output
        ))

    # --- Initialize pipelines ---
    pipelines = [CameraPipeline(cam, model_path) for cam in cameras]

    # Use the lowest FPS for synchronization
    fps = min(p.fps for p in pipelines)
    frame_count = 0
    start_time = time.time()

    # --- Main Loop ---
    while True:
        active_pipelines = 0
        for p in pipelines:
            ok = p.process_frame()
            if not ok:
                continue
            active_pipelines += 1

            # Save periodically
            if p.counter.periodic_save(interval=10, db_client=db_client):
                print(f"[SAVE] {p.camera.id} Counts at {frame_count / fps:.1f}s → {p.counter.counts}")

        if active_pipelines == 0:
            print("[INFO] All videos ended.")
            break

        frame_count += 1

        # Sync timing between cameras
        elapsed = time.time() - start_time
        expected = frame_count / fps
        if expected > elapsed:
            time.sleep(expected - elapsed)

        if frame_count % 30 == 0:
            print(f"Processed {frame_count} frames (≈ {frame_count / fps:.1f}s).")

    # --- Cleanup ---
    for p in pipelines:
        p.cleanup()
        print(f"Final counts → {p.camera.id}: {p.counter.counts}")
    db_client.close()


if __name__ == "__main__":
    main()
