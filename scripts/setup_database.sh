#!/bin/bash
# PostgreSQL + TimescaleDB Setup Script for MTP

set -e

echo "======================================================"
echo "MTP Database Setup - PostgreSQL + TimescaleDB"
echo "======================================================"

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL not found. Installing..."
    
    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Ubuntu/Debian
        sudo apt update
        sudo apt install -y postgresql-15 postgresql-contrib-15
        
        # Install TimescaleDB
        sudo add-apt-repository -y ppa:timescale/timescaledb-ppa
        sudo apt update
        sudo apt install -y timescaledb-2-postgresql-15
        
        # Tune PostgreSQL
        sudo timescaledb-tune --quiet --yes
        
        # Restart PostgreSQL
        sudo systemctl restart postgresql
        
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install postgresql@15 timescaledb
        
        # Configure TimescaleDB
        echo "shared_preload_libraries = 'timescaledb'" >> /usr/local/var/postgresql@15/postgresql.conf
        
        # Restart PostgreSQL
        brew services restart postgresql@15
    else
        echo "❌ Unsupported OS: $OSTYPE"
        exit 1
    fi
    
    echo "✅ PostgreSQL + TimescaleDB installed"
else
    echo "✅ PostgreSQL already installed"
fi

# Create database and user
echo ""
echo "Creating MTP database..."

sudo -u postgres psql <<EOF
-- Drop existing if needed
DROP DATABASE IF EXISTS mtp_db;
DROP USER IF EXISTS mtp_user;

-- Create database
CREATE DATABASE mtp_db;

-- Create user
CREATE USER mtp_user WITH PASSWORD 'mtp_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE mtp_db TO mtp_user;

-- Connect to database
\c mtp_db

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO mtp_user;

EOF

echo "✅ Database 'mtp_db' created"
echo "✅ User 'mtp_user' created with password 'mtp_password'"
echo ""
echo "Connection string:"
echo "postgresql+asyncpg://mtp_user:mtp_password@localhost:5432/mtp_db"
echo ""
echo "======================================================"
echo "✅ MTP Database Setup Complete"
echo "======================================================"
echo ""
echo "Next steps:"
echo "1. Update /app/backend/.env with POSTGRES_URL"
echo "2. Run: cd /app/backend && uvicorn server:app --reload"
echo ""
