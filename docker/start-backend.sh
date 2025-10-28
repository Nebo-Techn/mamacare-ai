#!/bin/bash
set -e


echo "Initializing database ..."
python -m backend.pipeline.db.init_db init

echo "Running migration..."
python -m backend.pipeline.migration.migrate_existing_data


echo "Start FastAPI server..."
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
