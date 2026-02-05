"""
Database configuration module for log ingestion pipeline.
"""
import os
from typing import Dict
from dotenv import load_dotenv

load_dotenv()


def get_db_config() -> Dict[str, str]:
    """
    Get database configuration from environment variables.
    
    Returns:
        Dictionary containing database connection parameters
    """
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5431'),
        'database': os.getenv('DB_NAME', 'log_pipeline'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '12345')
    }


def get_db_connection_string() -> str:
    """
    Get PostgreSQL connection string.
    
    Returns:
        Connection string for psycopg2
    """
    config = get_db_config()
    return (
        f"host={config['host']} "
        f"port={config['port']} "
        f"dbname={config['database']} "
        f"user={config['user']} "
        f"password={config['password']}"
    )
