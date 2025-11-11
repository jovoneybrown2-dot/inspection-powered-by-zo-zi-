import os

# Use /tmp on Render (ephemeral storage), local file otherwise
# Check if we're on Render by looking for RENDER environment variable
IS_RENDER = os.getenv('RENDER') is not None

if IS_RENDER:
    DB_PATH = '/tmp/inspections.db'
else:
    DB_PATH = 'inspections.db'
