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

    def save_camera(self, cam_id, video_path, frame_width, frame_height, lines):
        query = """
            INSERT INTO cameras (cam_id, video_path, frame_width, frame_height, lines)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (cam_id)
            DO UPDATE SET
                video_path = EXCLUDED.video_path,
                frame_width = EXCLUDED.frame_width,
                frame_height = EXCLUDED.frame_height,
                lines = EXCLUDED.lines,
                created_at = NOW();
        """
        with self.conn.cursor() as cur:
            cur.execute(
                query,
                (cam_id, video_path, frame_width, frame_height, json.dumps(lines))
            )

    def get_registered_cameras(self):
        """
        Returns a list of cameras registered in the database.
        Each camera is a dict: {"cam_id": str, "video_path": str, "lines": list of tuples}
        """
        query = "SELECT cam_id, video_path, lines FROM cameras;"
        cameras = []
        with self.conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            for cam_id, video_path, lines_list in rows:
                # lines_list is already a Python list from JSONB
                lines = [tuple(line) for line in lines_list]
                cameras.append({
                    "cam_id": cam_id,
                    "video_path": video_path,
                    "lines": lines
                })
        return cameras

    def close(self):
        if self.conn:
            self.conn.close()
