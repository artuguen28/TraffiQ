CREATE TABLE IF NOT EXISTS cameras (
    id SERIAL PRIMARY KEY,
    cam_id VARCHAR(50) UNIQUE NOT NULL,
    video_path TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    frame_width INTEGER NOT NULL CHECK (frame_width > 0),
    frame_height INTEGER NOT NULL CHECK (frame_height > 0),
    lines JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS traffic_summary (
    id SERIAL PRIMARY KEY,
    cam_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    lane_counts JSONB NOT NULL,
    max_cars_in_frame INTEGER NOT NULL CHECK (max_cars_in_frame >= 0),

    CONSTRAINT fk_traffic_summary_camera
        FOREIGN KEY (cam_id)
        REFERENCES cameras (cam_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_traffic_summary_timestamp
    ON traffic_summary (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_traffic_summary_cam_timestamp
    ON traffic_summary (cam_id, timestamp DESC);
