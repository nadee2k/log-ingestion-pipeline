# Application Log Ingestion & Analytics Pipeline

A production-ready data engineering project that ingests raw application logs, transforms them into structured analytics tables, and exposes metrics via a REST API.

## 📋 Problem Statement

Modern distributed systems generate massive volumes of log data. This pipeline addresses the challenge of:
- **Ingesting** raw application logs from various services
- **Structuring** unstructured log data into queryable formats
- **Analyzing** logs to answer operational questions like:
  - How many errors occurred per service per day?
  - Which endpoints have the highest latency?
  - What services are failing most frequently?

## 🏗️ Architecture Overview

```
Raw Logs (JSON)
      ↓
Ingestion (Python)
      ↓
PostgreSQL (Staging)
      ↓
Transformation (SQL + Python)
      ↓
Analytics Tables
      ↓
FastAPI (Metrics API)
```

## 🛠️ Tech Stack

- **Language**: Python 3.11+
- **Database**: PostgreSQL 15
- **API Framework**: FastAPI
- **Data Processing**: pandas, psycopg2
- **Containerization**: Docker & Docker Compose
- **Environment Management**: python-dotenv

## 📁 Project Structure

```
log-ingestion-pipeline/
│
├── data/
│   └── raw_logs.json          # Sample log data
│
├── src/
│   ├── config/
│   │   └── db_config.py        # Database configuration
│   │
│   ├── ingestion/
│   │   └── ingest_logs.py      # Log ingestion script
│   │
│   ├── transformation/
│   │   └── transform_logs.py   # ETL transformation logic
│   │
│   ├── api/
│   │   └── main.py             # FastAPI application
│   │
│   └── utils/
│       └── logger.py            # Logging utilities
│
├── sql/
│   ├── create_tables.sql       # Database schema
│   └── analytics_queries.sql   # Sample analytics queries
│
├── docker/
│   ├── Dockerfile              # API service container
│   └── docker-compose.yml      # Multi-container setup
│
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
└── README.md                   # This file
```

## 🗄️ Database Schema

### Staging Table
```sql
staging_logs (
    id, timestamp, service, level, endpoint,
    response_time_ms, status_code, message, ingestion_time
)
```

### Analytics Tables
- **daily_error_counts**: Error counts per service per day
- **endpoint_latency**: Average response time per endpoint
- **service_health**: Comprehensive service health metrics

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+ (or use Docker)
- Docker & Docker Compose (optional)

### Option 1: Local Setup

1. **Install system dependencies** (if needed)
   ```bash
   # On Fedora/RHEL:
   sudo dnf install postgresql-devel python3-devel gcc
   
   # On Ubuntu/Debian:
   sudo apt-get install libpq-dev python3-dev gcc
   ```

2. **Clone and setup environment**
   ```bash
   cd log-ingestion-pipeline
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Configure database**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Start PostgreSQL** (if not already running)
   ```bash
   # Check if PostgreSQL is running
   sudo systemctl status postgresql
   
   # If not running, start it:
   sudo systemctl start postgresql
   sudo systemctl enable postgresql  # Enable auto-start on boot
   
   # Create database if it doesn't exist
   sudo -u postgres psql -c "CREATE DATABASE log_pipeline;" || echo "Database may already exist"
   ```

5. **Initialize database**
   ```bash
   psql -U postgres -d log_pipeline -f sql/create_tables.sql
   ```
   
   **Note:** If you get a connection error, try:
   ```bash
   sudo -u postgres psql -d log_pipeline -f sql/create_tables.sql
   ```

6. **Ingest sample data**
   ```bash
   python -m src.ingestion.ingest_logs data/raw_logs.json
   ```

7. **Run transformations**
   ```bash
   python -m src.transformation.transform_logs
   ```

8. **Start API server**
   ```bash
   python -m src.api.main
   # Or: uvicorn src.api.main:app --reload
   ```

### Option 2: Docker Setup (Recommended)

1. **Start all services**
   ```bash
   docker-compose up -d
   ```

2. **Wait for services to be healthy** (check with `docker-compose ps`)

3. **Ingest data**
   ```bash
   docker-compose exec api python -m src.ingestion.ingest_logs data/raw_logs.json
   ```

4. **Run transformations**
   ```bash
   docker-compose exec api python -m src.transformation.transform_logs
   ```

## 🔧 Troubleshooting

### psycopg2-binary Installation Error

If you encounter an error like `Error: pg_config executable not found` when installing `psycopg2-binary`, you need to install PostgreSQL development libraries:

**On Fedora/RHEL:**
```bash
sudo dnf install postgresql-devel python3-devel gcc
```

**On Ubuntu/Debian:**
```bash
sudo apt-get install libpq-dev python3-dev gcc
```

**On macOS:**
```bash
brew install postgresql
```

Then retry the installation:
```bash
pip install -r requirements.txt
```

**Alternative:** If you're using Python 3.14 or a very new version, you can also try installing the latest psycopg2-binary directly:
```bash
pip install --upgrade psycopg2-binary
```

### Database Connection Issues

If you can't connect to PostgreSQL:

1. **PostgreSQL not running:**
   ```bash
   # Check status
   sudo systemctl status postgresql
   
   # Start PostgreSQL
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   ```

2. **Database doesn't exist:**
   ```bash
   # Create database
   sudo -u postgres psql -c "CREATE DATABASE log_pipeline;"
   ```

3. **Connection refused:**
   - Check your `.env` file has correct credentials
   - Verify PostgreSQL is listening: `sudo netstat -tlnp | grep 5431`
   - Check PostgreSQL config: `sudo cat /var/lib/pgsql/data/postgresql.conf | grep listen_addresses`

4. **Permission denied:**
   - You may need to use `sudo -u postgres psql` instead of `psql -U postgres`
   - Or configure PostgreSQL to allow local connections without password

**Tip:** If you're having trouble with local PostgreSQL, use Docker instead (see Option 2) - it's much easier!

### Docker Issues

If Docker containers fail to start:
1. Check logs: `docker-compose logs`
2. Ensure ports 5431 and 8000 are not already in use
3. Try rebuilding: `docker-compose build --no-cache`

## 📡 API Endpoints

### Base URL
```
http://localhost:8000
```

### Available Endpoints

#### 1. Health Check
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

#### 2. Error Metrics
```bash
GET /metrics/errors?service=auth-service&start_date=2026-01-10
```

**Response:**
```json
{
  "data": [
    {
      "log_date": "2026-01-10",
      "service": "auth-service",
      "error_count": 3
    }
  ],
  "count": 1
}
```

#### 3. Latency Metrics
```bash
GET /metrics/latency?min_requests=5
```

**Response:**
```json
{
  "data": [
    {
      "endpoint": "/login",
      "avg_response_time_ms": 456.5,
      "request_count": 10,
      "last_updated": "2026-01-10T15:30:00"
    }
  ],
  "count": 1
}
```

#### 4. Service Health
```bash
GET /metrics/health?service=auth-service
```

**Response:**
```json
{
  "data": [
    {
      "service": "auth-service",
      "log_date": "2026-01-10",
      "total_requests": 15,
      "error_count": 3,
      "success_count": 12,
      "avg_response_time_ms": 345.2,
      "error_rate_percent": 20.0
    }
  ],
  "count": 1
}
```

### Interactive API Documentation
Visit `http://localhost:8000/docs` for Swagger UI or `http://localhost:8000/redoc` for ReDoc.

## 📊 Sample Queries

See `sql/analytics_queries.sql` for example SQL queries you can run directly against the database.

## 🔧 Usage Examples

### Ingest Logs
```bash
# Single file
python -m src.ingestion.ingest_logs data/raw_logs.json

# With custom batch size
python -m src.ingestion.ingest_logs data/raw_logs.json --batch-size 50
```

### Run Transformations
```bash
python -m src.transformation.transform_logs
```

### Query API
```bash
# Get all errors
curl http://localhost:8000/metrics/errors

# Get errors for specific service
curl http://localhost:8000/metrics/errors?service=auth-service

# Get latency metrics
curl http://localhost:8000/metrics/latency?min_requests=10
```

## 🧪 Testing

```bash
# Run API health check
curl http://localhost:8000/health

# Test ingestion
python -m src.ingestion.ingest_logs data/raw_logs.json

# Test transformation
python -m src.transformation.transform_logs

# Verify data in database
psql -U postgres -d log_pipeline -c "SELECT * FROM daily_error_counts LIMIT 5;"
```

## 📈 Resume Bullet Point

> Built a log ingestion and analytics pipeline processing raw application logs into structured PostgreSQL analytics tables, enabling service-level error and latency monitoring via a FastAPI metrics API. Implemented ETL workflows with batch processing, data validation, and automated transformation jobs.

## 🎯 Key Features

- ✅ **ETL Pipeline**: Complete extract, transform, load workflow
- ✅ **Data Validation**: Schema validation and error handling
- ✅ **Batch Processing**: Efficient bulk inserts
- ✅ **Analytics Tables**: Pre-aggregated metrics for fast queries
- ✅ **REST API**: FastAPI with automatic documentation
- ✅ **Docker Support**: Production-ready containerization
- ✅ **Error Handling**: Comprehensive logging and error management
- ✅ **Scalable Design**: Indexed tables and optimized queries

## 🔐 Environment Variables

Create a `.env` file based on `.env.example`:

```env
DB_HOST=localhost
DB_PORT=5431
DB_NAME=log_pipeline
DB_USER=postgres
DB_PASSWORD=postgres
```

## 📝 License

This project is for educational and portfolio purposes.

## 🤝 Contributing

This is a portfolio project, but suggestions and improvements are welcome!

---


