#!/usr/bin/env bash
apt-get update
apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
pip install -r requirements.txt

# Run database migrations
python migrate_postgres_schema.py