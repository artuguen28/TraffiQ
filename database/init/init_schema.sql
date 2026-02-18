-- ============================================
-- TRAFFIQ DATABASE SCHEMA WITH TIMESCALEDB
-- ============================================
-- Simplified schema matching actual application usage

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ============================================
-- CAMERAS TABLE
-- ============================================
-- Stores camera configuration including lane line definitions
CREATE TABLE IF NOT EXISTS cameras (
    id SERIAL PRIMARY KEY,
    cam_id VARCHAR(50) UNIQUE NOT NULL,
    video_path TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    frame_width INTEGER NOT NULL CHECK (frame_width > 0),
    frame_height INTEGER NOT NULL CHECK (frame_height > 0),
    lines JSONB NOT NULL  -- Array of line segments: [[x1,y1,x2,y2], ...]
);

-- ============================================
-- TRAFFIC SUMMARY (Time-series data)
-- ============================================
-- Stores periodic snapshots of vehicle counts per camera
CREATE TABLE IF NOT EXISTS traffic_summary (
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    cam_id VARCHAR(50) NOT NULL,
    lane_counts JSONB NOT NULL,  -- Array of counts per lane: [count_lane1, count_lane2, ...]
    max_cars_in_frame INTEGER NOT NULL DEFAULT 0 CHECK (max_cars_in_frame >= 0),

    CONSTRAINT fk_traffic_summary_camera
        FOREIGN KEY (cam_id)
        REFERENCES cameras (cam_id)
        ON DELETE CASCADE
);

-- Convert to TimescaleDB hypertable for efficient time-series queries
SELECT create_hypertable(
    'traffic_summary',
    'timestamp',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '1 day'
);

-- ============================================
-- INDEX FOR COMMON QUERIES
-- ============================================
CREATE INDEX IF NOT EXISTS idx_traffic_summary_cam_timestamp
    ON traffic_summary (cam_id, timestamp DESC);

-- ============================================
-- COMPRESSION POLICY (Save storage on old data)
-- ============================================
SELECT add_compression_policy('traffic_summary',
    INTERVAL '7 days',
    if_not_exists => TRUE
);

-- ============================================
-- USEFUL VIEW
-- ============================================
-- Get the most recent traffic status for each camera
CREATE OR REPLACE VIEW latest_traffic_status AS
SELECT DISTINCT ON (cam_id)
    cam_id,
    timestamp,
    lane_counts,
    max_cars_in_frame
FROM traffic_summary
ORDER BY cam_id, timestamp DESC;

-- ============================================
-- EXAMPLE QUERIES FOR RAG CHATBOT
-- ============================================
/*
-- Total vehicles in last hour for a camera (sum all lanes)
SELECT
    cam_id,
    timestamp,
    (SELECT SUM(value::int) FROM jsonb_array_elements_text(lane_counts) AS value) as total_vehicles
FROM traffic_summary
WHERE cam_id = 'CAM_01' AND timestamp > NOW() - INTERVAL '1 hour';

-- Peak traffic moments (top 10)
SELECT timestamp, cam_id, max_cars_in_frame
FROM traffic_summary
ORDER BY max_cars_in_frame DESC
LIMIT 10;

-- Average vehicles per snapshot for each camera
SELECT
    cam_id,
    AVG((SELECT SUM(value::int) FROM jsonb_array_elements_text(lane_counts) AS value)) as avg_vehicles
FROM traffic_summary
GROUP BY cam_id;

-- Traffic over time for a camera (last 24 hours, grouped by hour)
SELECT
    date_trunc('hour', timestamp) as hour,
    AVG((SELECT SUM(value::int) FROM jsonb_array_elements_text(lane_counts) AS value)) as avg_vehicles,
    MAX(max_cars_in_frame) as peak_vehicles
FROM traffic_summary
WHERE cam_id = 'CAM_01' AND timestamp > NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour;
*/