"""
Log ingestion module for processing raw JSON logs into staging table.
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config.db_config import get_db_engine
from utils.logger import setup_logger

logger = setup_logger(__name__)


def validate_log_entry(log: Dict[str, Any]) -> bool:
    """
    Validate a log entry has required fields.
    
    Args:
        log: Dictionary containing log entry
    
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['timestamp', 'service', 'level']
    return all(field in log for field in required_fields)


def parse_timestamp(timestamp_str: str) -> str:
    """
    Parse timestamp string to PostgreSQL format.
    
    Args:
        timestamp_str: ISO format timestamp string
    
    Returns:
        Formatted timestamp string
    """
    try:
        from datetime import datetime
        # Try parsing ISO format
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logger.warning(f"Failed to parse timestamp {timestamp_str}: {e}")
        return None


def ingest_logs(file_path: str, batch_size: int = 100) -> int:
    """
    Ingest logs from JSON file into staging_logs table.
    
    Args:
        file_path: Path to JSON file containing logs
        batch_size: Number of records to insert per batch
    
    Returns:
        Number of records successfully ingested
    """
    logger.info(f"Starting ingestion from {file_path}")
    
    # Read JSON file
    try:
        with open(file_path, 'r') as f:
            logs = json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return 0
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in file {file_path}: {e}")
        return 0
    
    if not isinstance(logs, list):
        logger.error("JSON file must contain a list of log entries")
        return 0
    
    logger.info(f"Found {len(logs)} log entries to process")
    
    # Connect to database
    try:
        engine = get_db_engine()
        conn = engine.connect()
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return 0
    
    # Prepare valid log entries
    valid_logs = []
    invalid_count = 0
    
    for log in logs:
        if not validate_log_entry(log):
            invalid_count += 1
            logger.debug(f"Invalid log entry (missing required fields): {log}")
            continue
        
        timestamp = parse_timestamp(log.get('timestamp'))
        if not timestamp:
            invalid_count += 1
            continue
        
        valid_logs.append((
            timestamp,
            log.get('service'),
            log.get('level'),
            log.get('endpoint'),
            log.get('response_time_ms'),
            log.get('status_code'),
            log.get('message')
        ))
    
    if invalid_count > 0:
        logger.warning(f"Skipped {invalid_count} invalid log entries")
    
    # Batch insert into staging table
    try:
        for log_entry in valid_logs:
            conn.execute(text("""
                INSERT INTO staging_logs 
                (timestamp, service, level, endpoint, response_time_ms, status_code, message)
                VALUES (:ts, :service, :level, :endpoint, :response_time, :status_code, :message)
            """), {
                'ts': log_entry[0],
                'service': log_entry[1],
                'level': log_entry[2],
                'endpoint': log_entry[3],
                'response_time': log_entry[4],
                'status_code': log_entry[5],
                'message': log_entry[6]
            })
        
        conn.commit()
        ingested_count = len(valid_logs)
        logger.info(f"Successfully ingested {ingested_count} log entries")
        return ingested_count
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to insert logs: {e}")
        return 0
    finally:
        conn.close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Ingest logs from JSON file')
    parser.add_argument('file_path', type=str, help='Path to JSON log file')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for inserts')
    
    args = parser.parse_args()
    
    count = ingest_logs(args.file_path, args.batch_size)
    sys.exit(0 if count > 0 else 1)
