import time
import random
import psycopg2
from datetime import datetime
from threading import Thread

# Database connection parameters
DB_CONFIG = {
    "dbname": "traffic_db",
    "user": "traffic_user",
    "password": "traffic_pass",
    "host": "localhost",
    "port": 5432
}

def connect_db():
    return psycopg2.connect(**DB_CONFIG)

def insert_traffic_data(conn, cam_id, lane_counts, max_cars):
    with conn.cursor() as cur:
        query = """
            INSERT INTO traffic_summary (
                cam_id, timestamp, lane_1_count, lane_2_count, lane_3_count, max_cars_in_frame
            )
            VALUES (%s, NOW(), %s, %s, %s, %s);
        """
        cur.execute(query, (cam_id, lane_counts[0], lane_counts[1], lane_counts[2], max_cars))
    conn.commit()

def simulate_lane_counts(phase):
    """Generate realistic traffic for each intensity phase."""
    if phase == "low":
        lane_1 = random.randint(0, 2)
        lane_2 = random.randint(0, 3)
        lane_3 = random.randint(0, 2)
    elif phase == "medium":
        lane_1 = random.randint(2, 5)
        lane_2 = random.randint(3, 6)
        lane_3 = random.randint(2, 5)
    else:  # high
        lane_1 = random.randint(5, 10)
        lane_2 = random.randint(6, 12)
        lane_3 = random.randint(5, 10)

    max_cars = sum([lane_1, lane_2, lane_3]) + random.randint(0, 5)
    return [lane_1, lane_2, lane_3], max_cars

def simulate_camera(cam_id, phases, interval=7, duration=300):
    """
    Simulate a single camera with alternating traffic phases.
    duration: total time to run (seconds).
    """
    conn = connect_db()
    start_time = time.time()
    cycle = 0
    print(f"Started simulation for {cam_id}")

    try:
        while time.time() - start_time < duration:
            phase = phases[cycle % len(phases)]
            lane_counts, max_cars = simulate_lane_counts(phase)
            insert_traffic_data(conn, cam_id, lane_counts, max_cars)

            print(f"[{datetime.now().strftime('%H:%M:%S')}] {cam_id} | "
                  f"Phase={phase.upper()} | L1={lane_counts[0]} | "
                  f"L2={lane_counts[1]} | L3={lane_counts[2]} | Max={max_cars}")

            time.sleep(interval)
            cycle += 1

    except KeyboardInterrupt:
        print(f"\nStopping {cam_id} manually.")
    finally:
        conn.close()
        print(f"Simulation for {cam_id} finished.")

def main():
    # Define different traffic phase progressions for each camera
    cam1_phases = ["low", "medium", "high", "medium"]  # increasing traffic
    cam2_phases = ["high", "medium", "low", "medium"]  # decreasing traffic

    duration_seconds = 5 * 60  # 5 minutes total
    interval_seconds = 10

    cam1_thread = Thread(target=simulate_camera, args=("CAM_01", cam1_phases, interval_seconds, duration_seconds))
    cam2_thread = Thread(target=simulate_camera, args=("CAM_02", cam2_phases, interval_seconds, duration_seconds))

    cam1_thread.start()
    cam2_thread.start()

    cam1_thread.join()
    cam2_thread.join()

    print("✅ Simulation completed for all cameras.")

if __name__ == "__main__":
    main()
