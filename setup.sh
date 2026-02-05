#!/bin/bash

# Setup script for Log Ingestion Pipeline

# Don't exit on error for pg_config check
set +e

echo "🚀 Setting up Log Ingestion Pipeline..."

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found Python $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip

# Check if psycopg2-binary installation might fail
echo "🔍 Checking for PostgreSQL development libraries..."
if ! command -v pg_config &> /dev/null; then
    echo "⚠️  Warning: pg_config not found. psycopg2-binary might fail to install."
    echo "   Install PostgreSQL dev libraries:"
    echo "   Fedora/RHEL: sudo dnf install postgresql-devel python3-devel gcc"
    echo "   Ubuntu/Debian: sudo apt-get install libpq-dev python3-dev gcc"
    echo "   Then re-run: pip install -r requirements.txt"
    echo ""
fi

echo "📦 Installing Python packages..."
set -e  # Exit on error for pip install
pip install -r requirements.txt
set +e  # Don't exit on error for remaining checks

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "   Please edit .env with your database credentials"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Start PostgreSQL (if not running):"
echo "   sudo systemctl start postgresql"
echo "   sudo -u postgres psql -c 'CREATE DATABASE log_pipeline;'"
echo ""
echo "2. Edit .env with your database credentials"
echo ""
echo "3. Initialize database:"
echo "   psql -U postgres -d log_pipeline -f sql/create_tables.sql"
echo "   (If that fails, try: sudo -u postgres psql -d log_pipeline -f sql/create_tables.sql)"
echo ""
echo "4. Ingest data: python -m src.ingestion.ingest_logs data/raw_logs.json"
echo "5. Run transformations: python -m src.transformation.transform_logs"
echo "6. Start API: python -m src.api.main"
echo ""
echo "💡 Tip: Using Docker is easier - no local PostgreSQL setup needed:"
echo "   docker-compose up -d"
