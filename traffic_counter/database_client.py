import os
import psycopg2
import json

class DatabaseClient:
    def __init__(self, host="localhost", db="traffic_db", user="traffic_user", password="traffic_pass", port=5432):
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            self.conn = psycopg2.connect(db_url)
        else:
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

    def delete_camera(self, cam_id: str):
        query = "DELETE FROM cameras WHERE cam_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (cam_id,))

    def get_traffic_summary(self, cam_id=None, from_ts=None, to_ts=None):
        conditions = []
        params = []

        if cam_id:
            conditions.append("cam_id = %s")
            params.append(cam_id)
        if from_ts:
            conditions.append("timestamp >= %s")
            params.append(from_ts)
        if to_ts:
            conditions.append("timestamp <= %s")
            params.append(to_ts)

        where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        query = f"SELECT * FROM traffic_summary {where_clause} ORDER BY timestamp DESC LIMIT 100;"

        with self.conn.cursor() as cur:
            cur.execute(query, params)
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def get_live_traffic(self):
        query = """
            SELECT DISTINCT ON (cam_id) cam_id, timestamp, lane_counts, max_cars_in_frame
            FROM traffic_summary
            ORDER BY cam_id, timestamp DESC;
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def close(self):
        if self.conn:
            self.conn.close()
