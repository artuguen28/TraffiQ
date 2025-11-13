import psycopg2
from datetime import datetime

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
            INSERT INTO traffic_summary (
                cam_id, timestamp, lane_1_count, lane_2_count, lane_3_count, max_cars_in_frame
            )
            VALUES (%s, NOW(), %s, %s, %s, %s);
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (cam_id, lane_counts[0], lane_counts[1], lane_counts[2], max_cars))
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()
