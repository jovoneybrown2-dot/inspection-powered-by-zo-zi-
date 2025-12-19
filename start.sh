#!/bin/bash
# Render startup script - initializes database and starts gunicorn

echo "🔄 Initializing database and syncing checklists..."
python reset_db.py

echo "🚀 Starting gunicorn..."
gunicorn app:app --bind 0.0.0.0:$PORT
