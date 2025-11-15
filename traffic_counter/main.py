import time
from camera import Camera
from database_client import DatabaseClient
from detection_pipeline import CameraPipeline


def main():
    # --- Define lanes for each camera ---

    model_path = "model/yolo12l.pt"

    cam_01 = Camera(
        cam_id="CAM_01",
        lanes=[
            (0, 1000, 650, 1000), 
            (800, 1000, 1100, 1000), 
            (1200, 1000, 1600, 1000)
        ],
        camera_video="traffic_cameras/camera_01.mp4",
        detection_output="cam1_tracked_output.mp4"
    )

    cam_02 = Camera(
        cam_id="CAM_02",
        lanes=[
            (400, 700, 850, 700), 
            (1000, 700, 1500, 700)
        ],
        camera_video="traffic_cameras/camera_02.mp4",
        detection_output="cam2_tracked_output.mp4"
    )

    # --- Initialize pipelines ---
    pipelines = [CameraPipeline(cam, model_path) for cam in [cam_01, cam_02]]
    db_client = DatabaseClient()

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