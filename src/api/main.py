"""
FastAPI application for log analytics metrics API.
"""
import sys
from pathlib import Path
from typing import List, Optional
from datetime import date, datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config.db_config import get_db_engine
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
        engine = get_db_engine()
        return engine.connect()
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
        result = conn.execute(text("SELECT 1"))
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
        
        query = """
            SELECT log_date, service, error_count
            FROM daily_error_counts
            WHERE 1=1
        """
        params = {}
        
        if service:
            query += " AND service = :service"
            params['service'] = service
        
        if start_date:
            query += " AND log_date >= :start_date"
            params['start_date'] = start_date
        
        if end_date:
            query += " AND log_date <= :end_date"
            params['end_date'] = end_date
        
        query += " ORDER BY log_date DESC, error_count DESC"
        
        result = conn.execute(text(query), params)
        results = result.fetchall()
        
        conn.close()
        
        return {
            "data": [dict(row._mapping) for row in results],
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
        
        query = """
            SELECT endpoint, avg_response_time_ms, request_count, last_updated
            FROM endpoint_latency
            WHERE request_count >= :min_requests
        """
        params = {'min_requests': min_requests}
        
        if endpoint:
            query += " AND endpoint = :endpoint"
            params['endpoint'] = endpoint
        
        query += " ORDER BY avg_response_time_ms DESC"
        
        result = conn.execute(text(query), params)
        results = result.fetchall()
        
        conn.close()
        
        return {
            "data": [dict(row._mapping) for row in results],
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
        
        query = """
            SELECT 
                service,
                log_date,
                total_requests,
                error_count,
                success_count,
                avg_response_time_ms,
                ROUND((error_count * 1.0 / CASE WHEN total_requests = 0 THEN 1 ELSE total_requests END) * 100, 2) as error_rate_percent
            FROM service_health
            WHERE 1=1
        """
        params = {}
        
        if service:
            query += " AND service = :service"
            params['service'] = service
        
        if log_date:
            query += " AND log_date = :log_date"
            params['log_date'] = log_date
        else:
            query += " AND log_date = DATE('now')"
        
        query += " ORDER BY error_rate_percent DESC"
        
        result = conn.execute(text(query), params)
        results = result.fetchall()
        
        conn.close()
        
        return {
            "data": [dict(row._mapping) for row in results],
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Error fetching service health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
