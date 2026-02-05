-- ============================================
-- Analytics Queries for Log Pipeline
-- ============================================

-- Query 1: Get daily error counts for all services
SELECT 
    log_date,
    service,
    error_count
FROM daily_error_counts
ORDER BY log_date DESC, error_count DESC;

-- Query 2: Get average latency per endpoint
SELECT 
    endpoint,
    avg_response_time_ms,
    request_count,
    last_updated
FROM endpoint_latency
ORDER BY avg_response_time_ms DESC;

-- Query 3: Get service health summary for a specific date
SELECT 
    service,
    log_date,
    total_requests,
    error_count,
    success_count,
    avg_response_time_ms,
    ROUND((error_count::FLOAT / NULLIF(total_requests, 0)) * 100, 2) as error_rate_percent
FROM service_health
WHERE log_date = CURRENT_DATE
ORDER BY error_rate_percent DESC;

-- Query 4: Top 5 services with most errors in last 7 days
SELECT 
    service,
    SUM(error_count) as total_errors
FROM daily_error_counts
WHERE log_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY service
ORDER BY total_errors DESC
LIMIT 5;

-- Query 5: Endpoints with highest latency
SELECT 
    endpoint,
    avg_response_time_ms,
    request_count
FROM endpoint_latency
WHERE request_count >= 10
ORDER BY avg_response_time_ms DESC
LIMIT 10;
