#!/bin/sh
set -e

echo "Waiting for database..."
until python -c "
import sys, time
from sqlalchemy import create_engine, text
from app.config import settings
try:
    create_engine(settings.database_url).connect().close()
except Exception as e:
    print(e)
    sys.exit(1)
"; do
  sleep 1
done

echo "Running migrations..."
alembic upgrade head

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
