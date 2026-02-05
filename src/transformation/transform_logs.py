"""
Transformation module for processing staging logs into analytics tables.
"""
import sys
from pathlib import Path
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config.db_config import get_db_connection_string
from utils.logger import setup_logger

logger = setup_logger(__name__)


def transform_to_daily_error_counts(conn) -> int:
    """
    Transform staging logs into daily_error_counts table.
    
    Args:
        conn: Database connection
    
    Returns:
        Number of records inserted/updated
    """
    cursor = conn.cursor()
    
    query = """
        INSERT INTO daily_error_counts (log_date, service, error_count)
        SELECT 
            DATE(timestamp) as log_date,
            service,
            COUNT(*) as error_count
        FROM staging_logs
        WHERE level = 'ERROR'
        GROUP BY DATE(timestamp), service
        ON CONFLICT (log_date, service) 
        DO UPDATE SET error_count = EXCLUDED.error_count
    """
    
    try:
        cursor.execute(query)
        conn.commit()
        count = cursor.rowcount
        logger.info(f"Updated daily_error_counts: {count} records")
        return count
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to update daily_error_counts: {e}")
        return 0
    finally:
        cursor.close()


def transform_to_endpoint_latency(conn) -> int:
    """
    Transform staging logs into endpoint_latency table.
    
    Args:
        conn: Database connection
    
    Returns:
        Number of records inserted/updated
    """
    cursor = conn.cursor()
    
    query = """
        INSERT INTO endpoint_latency (endpoint, avg_response_time_ms, request_count, last_updated)
        SELECT 
            endpoint,
            AVG(response_time_ms)::FLOAT as avg_response_time_ms,
            COUNT(*) as request_count,
            CURRENT_TIMESTAMP as last_updated
        FROM staging_logs
        WHERE endpoint IS NOT NULL 
          AND response_time_ms IS NOT NULL
        GROUP BY endpoint
        ON CONFLICT (endpoint) 
        DO UPDATE SET 
            avg_response_time_ms = EXCLUDED.avg_response_time_ms,
            request_count = EXCLUDED.request_count,
            last_updated = EXCLUDED.last_updated
    """
    
    try:
        cursor.execute(query)
        conn.commit()
        count = cursor.rowcount
        logger.info(f"Updated endpoint_latency: {count} records")
        return count
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to update endpoint_latency: {e}")
        return 0
    finally:
        cursor.close()


def transform_to_service_health(conn) -> int:
    """
    Transform staging logs into service_health table.
    
    Args:
        conn: Database connection
    
    Returns:
        Number of records inserted/updated
    """
    cursor = conn.cursor()
    
    query = """
        INSERT INTO service_health 
            (service, log_date, total_requests, error_count, success_count, avg_response_time_ms)
        SELECT 
            service,
            DATE(timestamp) as log_date,
            COUNT(*) as total_requests,
            SUM(CASE WHEN level = 'ERROR' THEN 1 ELSE 0 END) as error_count,
            SUM(CASE WHEN level IN ('INFO', 'DEBUG') OR status_code BETWEEN 200 AND 299 THEN 1 ELSE 0 END) as success_count,
            AVG(response_time_ms)::FLOAT as avg_response_time_ms
        FROM staging_logs
        GROUP BY service, DATE(timestamp)
        ON CONFLICT (service, log_date) 
        DO UPDATE SET 
            total_requests = EXCLUDED.total_requests,
            error_count = EXCLUDED.error_count,
            success_count = EXCLUDED.success_count,
            avg_response_time_ms = EXCLUDED.avg_response_time_ms
    """
    
    try:
        cursor.execute(query)
        conn.commit()
        count = cursor.rowcount
        logger.info(f"Updated service_health: {count} records")
        return count
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to update service_health: {e}")
        return 0
    finally:
        cursor.close()


def run_transformations() -> bool:
    """
    Run all transformation jobs.
    
    Returns:
        True if all transformations succeeded, False otherwise
    """
    logger.info("Starting transformation jobs")
    
    try:
        conn = psycopg2.connect(get_db_connection_string())
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return False
    
    try:
        # Run all transformations
        transform_to_daily_error_counts(conn)
        transform_to_endpoint_latency(conn)
        transform_to_service_health(conn)
        
        logger.info("All transformations completed successfully")
        return True
    except Exception as e:
        logger.error(f"Transformation failed: {e}")
        return False
    finally:
        conn.close()


if __name__ == '__main__':
    success = run_transformations()
    sys.exit(0 if success else 1)
