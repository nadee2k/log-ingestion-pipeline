-- ============================================
-- Database Schema for Log Ingestion Pipeline
-- ============================================

-- Staging Table (Raw Ingestion)
CREATE TABLE IF NOT EXISTS staging_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    service VARCHAR(50) NOT NULL,
    level VARCHAR(10) NOT NULL,
    endpoint VARCHAR(100),
    response_time_ms INT,
    status_code INT,
    message TEXT,
    ingestion_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_staging_timestamp ON staging_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_staging_service ON staging_logs(service);
CREATE INDEX IF NOT EXISTS idx_staging_level ON staging_logs(level);
CREATE INDEX IF NOT EXISTS idx_staging_endpoint ON staging_logs(endpoint);

-- Analytics Table: Daily Error Counts
CREATE TABLE IF NOT EXISTS daily_error_counts (
    log_date DATE NOT NULL,
    service VARCHAR(50) NOT NULL,
    error_count INT NOT NULL DEFAULT 0,
    PRIMARY KEY (log_date, service)
);

-- Analytics Table: Average Latency per Endpoint
CREATE TABLE IF NOT EXISTS endpoint_latency (
    endpoint VARCHAR(100) NOT NULL PRIMARY KEY,
    avg_response_time_ms FLOAT NOT NULL,
    request_count INT NOT NULL DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytics Table: Service Health Summary
CREATE TABLE IF NOT EXISTS service_health (
    service VARCHAR(50) NOT NULL,
    log_date DATE NOT NULL,
    total_requests INT NOT NULL DEFAULT 0,
    error_count INT NOT NULL DEFAULT 0,
    success_count INT NOT NULL DEFAULT 0,
    avg_response_time_ms FLOAT,
    PRIMARY KEY (service, log_date)
);
