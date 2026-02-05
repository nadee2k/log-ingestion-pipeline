"""
FastAPI application for log analytics metrics API.
"""
import sys
from pathlib import Path
from typing import List, Optional
from datetime import date, datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import psycopg2
from psycopg2.extras import RealDictCursor

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config.db_config import get_db_connection_string
from utils.logger import setup_logger

logger = setup_logger(__name__)
app = FastAPI(
    title="Log Analytics API",
    description="API for querying log ingestion pipeline metrics",
    version="1.0.0"
)


def get_db_connection():
    """Get database connection."""
    try:
        return psycopg2.connect(get_db_connection_string())
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Log Analytics API",
        "version": "1.0.0",
        "endpoints": {
            "/metrics/errors": "Get error counts by service and date",
            "/metrics/latency": "Get endpoint latency metrics",
            "/metrics/health": "Get service health summary",
            "/health": "API health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Database connection failed")


@app.get("/metrics/errors")
async def get_error_metrics(
    service: Optional[str] = Query(None, description="Filter by service name"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Get error counts by service and date.
    
    Query Parameters:
        service: Optional service name filter
        start_date: Optional start date filter
        end_date: Optional end date filter
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT log_date, service, error_count
            FROM daily_error_counts
            WHERE 1=1
        """
        params = []
        
        if service:
            query += " AND service = %s"
            params.append(service)
        
        if start_date:
            query += " AND log_date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND log_date <= %s"
            params.append(end_date)
        
        query += " ORDER BY log_date DESC, error_count DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "data": [dict(row) for row in results],
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Error fetching error metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics/latency")
async def get_latency_metrics(
    endpoint: Optional[str] = Query(None, description="Filter by endpoint"),
    min_requests: int = Query(1, description="Minimum request count")
):
    """
    Get average latency metrics per endpoint.
    
    Query Parameters:
        endpoint: Optional endpoint filter
        min_requests: Minimum number of requests to include
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT endpoint, avg_response_time_ms, request_count, last_updated
            FROM endpoint_latency
            WHERE request_count >= %s
        """
        params = [min_requests]
        
        if endpoint:
            query += " AND endpoint = %s"
            params.append(endpoint)
        
        query += " ORDER BY avg_response_time_ms DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "data": [dict(row) for row in results],
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Error fetching latency metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics/health")
async def get_service_health(
    service: Optional[str] = Query(None, description="Filter by service name"),
    log_date: Optional[date] = Query(None, description="Filter by date (defaults to today)")
):
    """
    Get service health summary.
    
    Query Parameters:
        service: Optional service name filter
        log_date: Optional date filter (defaults to today)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                service,
                log_date,
                total_requests,
                error_count,
                success_count,
                avg_response_time_ms,
                ROUND((error_count::FLOAT / NULLIF(total_requests, 0)) * 100, 2) as error_rate_percent
            FROM service_health
            WHERE 1=1
        """
        params = []
        
        if service:
            query += " AND service = %s"
            params.append(service)
        
        if log_date:
            query += " AND log_date = %s"
            params.append(log_date)
        else:
            query += " AND log_date = CURRENT_DATE"
        
        query += " ORDER BY error_rate_percent DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "data": [dict(row) for row in results],
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Error fetching service health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
