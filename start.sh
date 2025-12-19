#!/bin/bash
# Render startup script - resets database and starts gunicorn

echo "🔄 Resetting SQLite database to ensure correct schema..."
python reset_db.py

echo "🚀 Starting gunicorn..."
gunicorn app:app --bind 0.0.0.0:$PORT
