#! /usr/bin/env bash

set -e

# Run prestart script
bash scripts/prestart.sh

# Create initial data
python scripts/initial_data.py

# Start Uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
