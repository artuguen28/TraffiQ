CREATE TABLE IF NOT EXISTS traffic_summary (
    id SERIAL PRIMARY KEY,
    cam_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    lane_1_count INT NOT NULL,
    lane_2_count INT NOT NULL,
    lane_3_count INT NOT NULL,
    max_cars_in_frame INT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_traffic_summary_timestamp
ON traffic_summary (timestamp DESC);