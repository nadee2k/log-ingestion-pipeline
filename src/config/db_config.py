"""
Database configuration module for log ingestion pipeline.
"""
import os
from typing import Dict
from dotenv import load_dotenv
from sqlalchemy import create_engine, Engine

load_dotenv()


def get_db_config() -> Dict[str, str]:
    """
    Get database configuration from environment variables.
    
    Returns:
        Dictionary containing database connection parameters
    """
    db_type = os.getenv('DB_TYPE', 'sqlite')  # Default to sqlite for demo
    
    if db_type == 'sqlite':
        return {
            'type': 'sqlite',
            'database': os.getenv('DB_NAME', 'log_pipeline.db')
        }
    else:
        return {
            'type': 'postgres',
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5431'),
            'database': os.getenv('DB_NAME', 'log_pipeline'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '12345')
        }


def get_db_connection_string() -> str:
    """
    Get database connection string.
    
    Returns:
        Connection string for database
    """
    config = get_db_config()
    if config['type'] == 'sqlite':
        return f"sqlite:///{config['database']}"
    else:
        return (
            f"postgresql://{config['user']}:{config['password']}@"
            f"{config['host']}:{config['port']}/{config['database']}"
        )


def get_db_engine() -> Engine:
    """
    Get SQLAlchemy database engine.
    
    Returns:
        SQLAlchemy Engine instance
    """
    return create_engine(get_db_connection_string())
