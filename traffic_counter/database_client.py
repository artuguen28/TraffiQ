import psycopg2
import json

class DatabaseClient:
    def __init__(self, host="localhost", db="traffic_db", user="traffic_user", password="traffic_pass", port=5432):
        self.conn = psycopg2.connect(
            host=host,
            database=db,
            user=user,
            password=password,
            port=port
        )
        self.conn.autocommit = True

    def save_interval(self, cam_id, lane_counts, max_cars):
        query = """
            INSERT INTO traffic_summary (cam_id, lane_counts, max_cars_in_frame)
            VALUES (%s, %s, %s);
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (cam_id, json.dumps(lane_counts), max_cars))

    def save_camera(self, cam_id, frame_width, frame_height, lines):
        query = """
            INSERT INTO cameras (cam_id, frame_width, frame_height, lines)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (cam_id)
            DO UPDATE SET
                frame_width = EXCLUDED.frame_width,
                frame_height = EXCLUDED.frame_height,
                lines = EXCLUDED.lines,
                created_at = NOW();
        """
        with self.conn.cursor() as cur:
            cur.execute(
                query,
                (cam_id, frame_width, frame_height, json.dumps(lines))
            )

    def close(self):
        if self.conn:
            self.conn.close()
